"""
PetroNexa Physics Engine: Drilling Hydraulics & Diagnostic Analytics.
Pure-Python calculations isolated from presentation and web layers.

Model: Bingham Plastic drilling-hydraulics model with approximate 
laminar/turbulent flow regime detection.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math


@dataclass
class WellSegment:
    """Represents a discrete section of the wellbore geometry."""
    name: str
    top_depth_ft: float
    bottom_depth_ft: float
    pipe_od_in: float
    pipe_id_in: float
    hole_id_in: float
    mud_weight_ppg: float
    viscosity_cp: float
    yield_point_lb_100ft2: float

    def __post_init__(self):
        if self.bottom_depth_ft <= self.top_depth_ft:
            raise ValueError(
                f"Segment '{self.name}' bottom depth ({self.bottom_depth_ft} ft) "
                f"must exceed top depth ({self.top_depth_ft} ft)."
            )
        if self.pipe_od_in <= self.pipe_id_in:
            raise ValueError(
                f"Segment '{self.name}' pipe OD ({self.pipe_od_in} in) must exceed ID ({self.pipe_id_in} in)."
            )
        if self.hole_id_in <= self.pipe_od_in:
            raise ValueError(
                f"Segment '{self.name}' hole ID ({self.hole_id_in} in) must exceed pipe OD ({self.pipe_od_in} in)."
            )
        if self.mud_weight_ppg <= 0:
            raise ValueError(f"Segment '{self.name}' mud weight must be positive.")
        if self.viscosity_cp < 0 or self.yield_point_lb_100ft2 < 0:
            raise ValueError(f"Segment '{self.name}' rheology parameters cannot be negative.")

    @property
    def length_ft(self) -> float:
        return self.bottom_depth_ft - self.top_depth_ft


class DrillingHydraulicsEngine:
    """Bingham Plastic hydraulics calculation engine with flow-regime detection."""

    def __init__(
        self,
        surface_mud_weight_ppg: float,
        flow_rate_gpm: float,
        total_depth_ft: float,
        plastic_viscosity_cp: float,
        yield_point_lb_100ft2: float,
    ):
        if surface_mud_weight_ppg <= 0 or flow_rate_gpm <= 0 or total_depth_ft <= 0:
            raise ValueError("Mud weight, flow rate, and total depth must be strictly positive.")
        if plastic_viscosity_cp < 0 or yield_point_lb_100ft2 < 0:
            raise ValueError("Plastic viscosity and yield point cannot be negative.")

        self.mw = surface_mud_weight_ppg
        self.q = flow_rate_gpm
        self.td = total_depth_ft
        self.pv = max(0.1, plastic_viscosity_cp)
        self.yp = max(0.0, yield_point_lb_100ft2)
        self.segments: List[WellSegment] = []

    def add_segment(self, segment: WellSegment) -> None:
        self.segments.append(segment)

    def validate_segment_continuity(self) -> None:
        """Verifies that wellbore segments are contiguous and cover from surface to total depth."""
        if not self.segments:
            raise ValueError("No well segments defined.")

        sorted_segments = sorted(self.segments, key=lambda s: s.top_depth_ft)

        if not math.isclose(sorted_segments[0].top_depth_ft, 0.0, abs_tol=1e-2):
            raise ValueError(f"First segment must start at surface (0 ft), found {sorted_segments[0].top_depth_ft} ft.")

        for i in range(len(sorted_segments) - 1):
            curr_bottom = sorted_segments[i].bottom_depth_ft
            next_top = sorted_segments[i + 1].top_depth_ft
            if not math.isclose(curr_bottom, next_top, abs_tol=1e-2):
                raise ValueError(
                    f"Gap or overlap detected between segment '{sorted_segments[i].name}' "
                    f"bottom ({curr_bottom} ft) and '{sorted_segments[i+1].name}' top ({next_top} ft)."
                )

        if not math.isclose(sorted_segments[-1].bottom_depth_ft, self.td, abs_tol=1e-2):
            raise ValueError(
                f"Final segment bottom depth ({sorted_segments[-1].bottom_depth_ft} ft) "
                f"does not match Total Depth ({self.td} ft)."
            )

    def _calc_annular_velocity(self, hole_id: float, pipe_od: float) -> float:
        annular_area = (hole_id**2 - pipe_od**2) / 1029.4
        return self.q / annular_area if annular_area > 0 else 0.0

    def _calc_pipe_velocity(self, pipe_id: float) -> float:
        pipe_area = (pipe_id**2) / 1029.4
        return self.q / pipe_area if pipe_area > 0 else 0.0

    def _calc_annular_friction_loss(self, seg: WellSegment) -> float:
        v_a = self._calc_annular_velocity(seg.hole_id_in, seg.pipe_od_in)
        if v_a <= 0:
            return 0.0

        d_h = seg.hole_id_in - seg.pipe_od_in
        mu_e = seg.viscosity_cp + ((5.0 * seg.yield_point_lb_100ft2 * d_h) / v_a)
        reynolds = (928.0 * seg.mud_weight_ppg * v_a * d_h) / max(0.1, mu_e)

        if reynolds < 2100.0:
            dp_ft = (
                (seg.viscosity_cp * v_a / (1000.0 * (d_h**2))) 
                + (seg.yield_point_lb_100ft2 / (200.0 * d_h))
            )
        else:
            f_factor = 0.0791 / (reynolds**0.25)
            dp_ft = (f_factor * seg.mud_weight_ppg * (v_a**2)) / (25.8 * d_h * 10000.0)

        return max(0.0, dp_ft * seg.length_ft)

    def solve(self, validate_continuity: bool = True) -> Dict[str, Any]:
        if not self.segments:
            raise ValueError("No well segments added to hydraulics engine.")

        if validate_continuity:
            self.validate_segment_continuity()

        total_annular_dp = 0.0
        segment_breakdown = []

        for seg in self.segments:
            ann_dp = self._calc_annular_friction_loss(seg)
            total_annular_dp += ann_dp
            av = self._calc_annular_velocity(seg.hole_id_in, seg.pipe_od_in)
            pv_int = self._calc_pipe_velocity(seg.pipe_id_in)

            segment_breakdown.append({
                "segment_name": seg.name,
                "top_depth_ft": seg.top_depth_ft,
                "bottom_depth_ft": seg.bottom_depth_ft,
                "length_ft": seg.length_ft,
                "annular_velocity_ft_min": round(av, 2),
                "internal_pipe_velocity_ft_min": round(pv_int, 2),
                "annular_dp_psi": round(ann_dp, 2)
            })

        hydrostatic_psi = 0.052 * self.mw * self.td
        total_bhp_psi = hydrostatic_psi + total_annular_dp
        ecd_ppg = self.mw + (total_annular_dp / (0.052 * self.td))

        return {
            "surface_mud_weight_ppg": self.mw,
            "flow_rate_gpm": self.q,
            "total_depth_ft": self.td,
            "total_annular_dp_psi": round(total_annular_dp, 2),
            "hydrostatic_pressure_psi": round(hydrostatic_psi, 2),
            "bottom_hole_pressure_psi": round(total_bhp_psi, 2),
            "ecd_ppg": round(ecd_ppg, 2),
            "segment_breakdown": segment_breakdown
        }


class DiagnosticEngine:
    """Telemetry diagnostic analyzer for automated wellbore monitoring."""

    def __init__(self, ecd_upper_threshold_delta: float = 1.5, max_spp_limit: float = 3500.0):
        self.ecd_threshold_delta = ecd_upper_threshold_delta
        self.max_spp = max_spp_limit

    def analyze_telemetry(
        self, 
        physics_metrics: Dict[str, Any], 
        pore_limit: float,
        frac_limit: float,
        baseline_esd_ppg: Optional[float] = None,
        historical_esd: Optional[float] = None
    ) -> Dict[str, Any]:
        if pore_limit is None or frac_limit is None:
            raise ValueError(
                "Pore-pressure and fracture-gradient limits must be explicitly provided "
                "for hydraulic safety diagnostics."
            )

        ecd = physics_metrics.get("ecd_ppg", 0.0)
        spp = physics_metrics.get("standpipe_pressure_psi")

        base_density = baseline_esd_ppg if baseline_esd_ppg is not None else historical_esd
        if base_density is None:
            base_density = physics_metrics.get("surface_mud_weight_ppg", 0.0)

        delta_ecd = ecd - base_density
        flags = []
        severity = "GREEN"
        matched_hazard = "None"
        recommendations = []

        if ecd < pore_limit:
            severity = "RED"
            matched_hazard = "Underbalanced / Kick Risk"
            flags.append(f"ECD ({ecd:.2f} ppg) below formation pore pressure gradient ({pore_limit:.2f} ppg).")
            recommendations.append("Increase mud weight or reduce flow rate immediately to suppress potential influx.")
        elif ecd > frac_limit:
            severity = "RED"
            matched_hazard = "Formation Fracture / Severe Losses"
            flags.append(f"ECD ({ecd:.2f} ppg) exceeds formation fracture limit ({frac_limit:.2f} ppg).")
            recommendations.append("Reduce flow rate and mud density to avoid inducing losses into the formation.")
        elif delta_ecd >= self.ecd_threshold_delta:
            severity = "YELLOW"
            matched_hazard = "Excessive Annular Friction Spike"
            flags.append(f"ECD surge detected (+{round(delta_ecd, 2)} ppg over static baseline). Risk of formation fracturing.")
            recommendations.append("Monitor cuttings loading and evaluate hole cleaning sweeps.")
        elif delta_ecd > 0.8:
            severity = "YELLOW"
            matched_hazard = "Moderate Friction Surge"
            flags.append(f"Moderate friction surge (+{round(delta_ecd, 2)} ppg). Monitor hole cleaning.")
            recommendations.append("Perform high-viscosity pill sweep and track ECD trends.")

        if spp is not None and spp > self.max_spp:
            severity = "RED" if severity != "RED" else severity
            matched_hazard = "Standpipe Pressure Excursion"
            flags.append(f"Standpipe Pressure ({round(spp, 1)} psi) exceeds maximum limit ({self.max_spp} psi).")
            recommendations.append("Inspect surface equipment and check pipe for downhole restriction/packing.")

        if not recommendations:
            recommendations.append("Maintain standard flow rate and fluid properties within configured window.")

        detailed_diagnosis = (
            " ".join(flags) if flags 
            else f"Hydraulic state stable. Dynamic ECD of {ecd:.2f} ppg remains within configured limits."
        )

        return {
            "status": severity,
            "severity": severity,
            "delta_ecd_ppg": round(delta_ecd, 2),
            "baseline_esd_ppg": round(base_density, 2),
            "calculated_ecd_ppg": ecd,
            "standpipe_pressure_psi": spp,
            "flags": flags,
            "recommendation": recommendations[0],
            "pore_limit": round(pore_limit, 2),
            "frac_limit": round(frac_limit, 2),
            "matched_hazard": matched_hazard,
            "detailed_diagnosis": detailed_diagnosis,
            "actionable_recommendations": recommendations,
            "annular_dp_status": "CALCULATED",
        }
