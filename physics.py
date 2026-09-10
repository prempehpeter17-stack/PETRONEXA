"""
PetroNexa Physics Engine: Drilling Hydraulics & Diagnostic Analytics.
Pure-Python calculations isolated from presentation and web layers.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math


@dataclass
class WellSegment:
    """Represents a discrete section of the wellbore geometry."""
    name: str
    length_ft: float
    pipe_od_in: float
    pipe_id_in: float
    hole_id_in: float
    mud_weight_ppg: float
    viscosity_cp: float
    yield_point_lb_100ft2: float

    def __post_init__(self):
        if self.length_ft <= 0:
            raise ValueError(f"Segment '{self.name}' must have length > 0.")
        if self.pipe_od_in <= self.pipe_id_in:
            raise ValueError(f"Segment '{self.name}' pipe OD ({self.pipe_od_in}) must exceed ID ({self.pipe_id_in}).")
        if self.hole_id_in <= self.pipe_od_in:
            raise ValueError(f"Segment '{self.name}' hole ID ({self.hole_id_in}) must exceed pipe OD ({self.pipe_od_in}).")


class DrillingHydraulicsEngine:
    """Bingham Plastic hydraulics calculation engine."""

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
            
        self.mw = surface_mud_weight_ppg
        self.q = flow_rate_gpm
        self.td = total_depth_ft
        self.pv = max(0.1, plastic_viscosity_cp)
        self.yp = max(0.0, yield_point_lb_100ft2)
        self.segments: List[WellSegment] = []

    def add_segment(self, segment: WellSegment) -> None:
        self.segments.append(segment)

    def _calc_annular_velocity(self, hole_id: float, pipe_od: float) -> float:
        """Calculate annular velocity in feet per minute (ft/min)."""
        annular_area = (hole_id**2 - pipe_od**2) / 1029.4
        return self.q / annular_area if annular_area > 0 else 0.0

    def _calc_pipe_velocity(self, pipe_id: float) -> float:
        """Calculate internal pipe velocity in feet per minute (ft/min)."""
        pipe_area = (pipe_id**2) / 1029.4
        return self.q / pipe_area if pipe_area > 0 else 0.0

    def _calc_annular_friction_loss(self, seg: WellSegment) -> float:
        """Calculate annular pressure loss (psi) using Bingham Plastic model."""
        v_a = self.area_velocity = self._calc_annular_velocity(seg.hole_id_in, seg.pipe_od_in)
        d_h = seg.hole_id_in - seg.pipe_od_in
        
        # Effective viscosity (Bingham Plastic approximation)
        mu_e = seg.viscosity_cp + (5.0 * seg.yield_point_lb_100ft2 * d_h / max(v_a, 1.0))
        
        # Friction factor & pressure gradient (psi/ft)
        dp_ft = ((seg.mud_weight_ppg * v_a**2) / (25.8 * d_h * 10000.0)) + (
            (seg.yield_point_lb_100ft2 + (seg.viscosity_cp * v_a / (300.0 * d_h))) / (300.0 * d_h)
        )
        return max(0.0, dp_ft * seg.length_ft)

    def solve(self) -> Dict[str, Any]:
        """Calculates total hydraulic losses, ECD, and bit hydraulic horsepower."""
        if not self.segments:
            raise ValueError("No well segments added to hydraulics engine.")

        total_annular_dp = 0.0
        segment_breakdown = []

        for seg in self.segments:
            ann_dp = self._calc_annular_friction_loss(seg)
            total_annular_dp += ann_dp
            av = self._calc_annular_velocity(seg.hole_id_in, seg.pipe_od_in)
            
            segment_breakdown.append({
                "segment_name": seg.name,
                "length_ft": seg.length_ft,
                "annular_velocity_ft_min": round(av, 2),
                "annular_dp_psi": round(ann_dp, 2)
            })

        # Equivalent Circulating Density (ECD) in ppg
        ecd_ppg = self.mw + (total_annular_dp / (0.052 * self.td))
        
        # Hydrostatic Pressure in psi
        hydrostatic_psi = 0.052 * self.mw * self.td
        
        # Total Bottom Hole Pressure in psi
        total_bhp_psi = hydrostatic_psi + total_annular_dp

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
        historical_esd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyzes output metrics against historical baselines and safety thresholds.
        `historical_esd` represents Equivalent Static Density (baseline mud weight in ppg).
        """
        ecd = physics_metrics.get("ecd_ppg", 0.0)
        base_density = historical_esd if historical_esd is not None else physics_metrics.get("surface_mud_weight_ppg", 0.0)
        
        delta_ecd = ecd - base_density
        flags = []
        severity = "NORMAL"

        if delta_ecd >= self.ecd_threshold_delta:
            severity = "HIGH_RISK"
            flags.append(f"ECD surge detected (+{round(delta_ecd, 2)} ppg over static baseline). Risk of formation fracturing.")
        elif delta_ecd > 0.8:
            severity = "WARNING"
            flags.append(f"Moderate friction surge (+{round(delta_ecd, 2)} ppg). Monitor hole cleaning and cuttings loading.")

        return {
            "status": severity,
            "delta_ecd_ppg": round(delta_ecd, 2),
            "baseline_esd_ppg": base_density,
            "calculated_ecd_ppg": ecd,
            "flags": flags,
            "recommendation": "Maintain flow rate" if severity == "NORMAL" else "Consider reducing flow rate or sweeping hole."
        }
