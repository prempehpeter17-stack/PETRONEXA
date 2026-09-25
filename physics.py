"""PetroNexa drilling hydraulics and diagnostic calculation engine."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import math

class RheologyModel(str, Enum):
    BINGHAM_PLASTIC = "Bingham Plastic"
    POWER_LAW = "Power Law"
    HERSCHEL_BULKLEY = "Herschel-Bulkley"

@dataclass
class NozzleInput:
    size_in_32nds: int
    count: int = 1
    discharge_coefficient: float = 0.98
    def __post_init__(self):
        if self.size_in_32nds <= 0 or self.count <= 0:
            raise ValueError("Nozzle size and count must be positive.")

class WellSegment:
    """Well segment supporting both the current top/bottom API and legacy length API."""
    def __init__(self, name: str, top_depth_ft: float = 0.0, bottom_depth_ft: Optional[float] = None,
                 pipe_od_in: Optional[float] = None, pipe_id_in: Optional[float] = None,
                 hole_id_in: Optional[float] = None, mud_weight_ppg: float = 10.0,
                 viscosity_cp: float = 20.0, yield_point_lb_100ft2: float = 15.0,
                 length_ft: Optional[float] = None, inner_diameter_in: Optional[float] = None,
                 outer_diameter_in: Optional[float] = None):
        if pipe_od_in is None and outer_diameter_in is not None: pipe_od_in = outer_diameter_in
        if pipe_id_in is None and inner_diameter_in is not None: pipe_id_in = inner_diameter_in
        if pipe_od_in is None or pipe_id_in is None or hole_id_in is None:
            raise ValueError("Pipe OD, pipe ID and hole ID are required.")
        if length_ft is not None:
            top_depth_ft = float(top_depth_ft or 0.0)
            bottom_depth_ft = top_depth_ft + float(length_ft)
        if bottom_depth_ft is None:
            raise ValueError("Either bottom_depth_ft or length_ft must be supplied.")
        self.name=name; self.top_depth_ft=float(top_depth_ft); self.bottom_depth_ft=float(bottom_depth_ft)
        self.pipe_od_in=float(pipe_od_in); self.pipe_id_in=float(pipe_id_in); self.hole_id_in=float(hole_id_in)
        self.mud_weight_ppg=float(mud_weight_ppg); self.viscosity_cp=float(viscosity_cp)
        self.yield_point_lb_100ft2=float(yield_point_lb_100ft2)
        if self.bottom_depth_ft <= self.top_depth_ft: raise ValueError("Segment bottom depth must exceed top depth.")
        if self.pipe_od_in <= self.pipe_id_in: raise ValueError("Inner diameter (pipe ID) must be less than outer diameter (pipe OD).")
        if self.hole_id_in <= self.pipe_od_in: raise ValueError("Hole ID must exceed pipe OD.")
        if self.mud_weight_ppg <= 0: raise ValueError("Mud weight must be positive.")
        if self.viscosity_cp < 0 or self.yield_point_lb_100ft2 < 0: raise ValueError("Rheology values cannot be negative.")
    @property
    def length_ft(self): return self.bottom_depth_ft - self.top_depth_ft

class DrillingHydraulicsEngine:
    def __init__(self, surface_mud_weight_ppg: float, flow_rate_gpm: float, total_depth_ft: float,
                 plastic_viscosity_cp: float = 20.0, yield_point_lb_100ft2: float = 15.0,
                 rheology_model: RheologyModel = RheologyModel.BINGHAM_PLASTIC,
                 true_vertical_depth_ft: Optional[float] = None):
        if surface_mud_weight_ppg <= 0: raise ValueError("Invalid surface_mud_weight_ppg: must be greater than zero.")
        if flow_rate_gpm <= 0 or total_depth_ft <= 0: raise ValueError("Mud weight, flow rate, and total depth must be positive.")
        if true_vertical_depth_ft is not None and true_vertical_depth_ft > total_depth_ft:
            raise ValueError("TVD true_vertical_depth_ft cannot exceed Total Measured Depth")
        if plastic_viscosity_cp < 0 or yield_point_lb_100ft2 < 0: raise ValueError("Plastic viscosity and yield point cannot be negative.")
        self.mw=float(surface_mud_weight_ppg); self.q=float(flow_rate_gpm); self.td=float(total_depth_ft)
        self.pv=max(0.1,float(plastic_viscosity_cp)); self.yp=max(0.0,float(yield_point_lb_100ft2))
        self.rheology_model=rheology_model; self.tvd=float(true_vertical_depth_ft if true_vertical_depth_ft is not None else total_depth_ft); self.segments=[]; self.nozzles=[]
    def calculate_generalized_reynolds(self, velocity_fps, hydraulic_diameter_in, mud_weight_ppg, k_consistency, n_index):
        if velocity_fps <= 0 or hydraulic_diameter_in <= 0 or mud_weight_ppg <= 0 or k_consistency <= 0 or n_index <= 0:
            raise ValueError("Generalized Reynolds inputs must be positive.")
        # Common engineering screening form for power-law fluids. Inputs are field units.
        rho = mud_weight_ppg * 7.48052 / 32.174
        d_ft = hydraulic_diameter_in / 12.0
        return float((rho * (velocity_fps ** (2.0-n_index)) * (d_ft ** n_index)) / max(k_consistency * (8.0 ** (n_index-1.0)), 1e-12))
    def add_segment(self, segment): self.segments.append(segment)
    def add_nozzle(self, nozzle): self.nozzles.append(nozzle)
    def validate_segment_continuity(self):
        if not self.segments: raise ValueError("No well segments defined.")
        segs=sorted(self.segments,key=lambda x:x.top_depth_ft)
        if not math.isclose(segs[0].top_depth_ft,0,abs_tol=1e-2): raise ValueError("First segment must start at surface (0 ft).")
        for a,b in zip(segs,segs[1:]):
            if not math.isclose(a.bottom_depth_ft,b.top_depth_ft,abs_tol=1e-2): raise ValueError(f"Gap or overlap between '{a.name}' and '{b.name}'.")
        if not math.isclose(segs[-1].bottom_depth_ft,self.td,abs_tol=1e-2): raise ValueError("Final segment bottom must match Total Depth.")
    def _calc_annular_velocity(self,hole_id,pipe_od):
        area=(hole_id**2-pipe_od**2)/1029.4
        return self.q/area if area>0 else 0.0
    def _calc_pipe_velocity(self,pipe_id):
        area=(pipe_id**2)/1029.4
        return self.q/area if area>0 else 0.0
    def _calc_annular_friction_loss(self,seg):
        va=self._calc_annular_velocity(seg.hole_id_in,seg.pipe_od_in)
        if va<=0:return 0.0
        dh=seg.hole_id_in-seg.pipe_od_in
        mu_e=seg.viscosity_cp+(5*seg.yield_point_lb_100ft2*dh/max(va,0.1))
        reynolds=(928*seg.mud_weight_ppg*va*dh)/max(0.1,mu_e)
        if reynolds<2100:
            dp_ft=(seg.viscosity_cp*va/(1000*dh**2))+(seg.yield_point_lb_100ft2/(200*dh))
        else:
            f=0.0791/(reynolds**0.25)
            dp_ft=(f*seg.mud_weight_ppg*va**2)/(25.8*dh*10000)
        return max(0.0,dp_ft*seg.length_ft)
    def _estimate_nozzle_dp(self):
        if not self.nozzles:return 0.0
        # Standard field approximation: total nozzle area in square inches; pressure drop in psi.
        total_area=sum(n.count*math.pi*(n.size_in_32nds/32.0)**2/4 for n in self.nozzles)
        if total_area<=0:return 0.0
        return max(0.0, (self.q/(24.5*0.98*total_area))**2 * self.mw/8.33)
    def solve(self,validate_continuity=True):
        if not self.segments: raise ValueError("No well segments added to hydraulics engine.")
        if validate_continuity:self.validate_segment_continuity()
        total=0.0; breakdown=[]
        for seg in sorted(self.segments,key=lambda x:x.top_depth_ft):
            dp=self._calc_annular_friction_loss(seg); total+=dp
            breakdown.append({"segment_name":seg.name,"top_depth_ft":seg.top_depth_ft,"bottom_depth_ft":seg.bottom_depth_ft,"length_ft":seg.length_ft,"annular_velocity_ft_min":round(self._calc_annular_velocity(seg.hole_id_in,seg.pipe_od_in),2),"internal_pipe_velocity_ft_min":round(self._calc_pipe_velocity(seg.pipe_id_in),2),"annular_dp_psi":round(dp,2)})
        nozzle_dp=self._estimate_nozzle_dp(); hydro=0.052*self.mw*self.td; bhp=hydro+total
        ecd=self.mw+total/(0.052*self.td)
        spp=total+nozzle_dp
        return {"surface_mud_weight_ppg":self.mw,"flow_rate_gpm":self.q,"total_depth_ft":self.td,"total_annular_dp_psi":round(total,2),"total_annular_pressure_loss_psi":round(total,2),"hydrostatic_pressure_psi":round(hydro,2),"bottom_hole_pressure_psi":round(bhp,2),"ecd_ppg":round(ecd,2),"equivalent_circulating_density_ecd_ppg":round(ecd,2),"standpipe_pressure_psi":round(spp,2),"standpipe_pressure_spp_psi":round(spp,2),"nozzle_pressure_drop_psi":round(nozzle_dp,2),"segment_breakdown":breakdown}

class DiagnosticEngine:
    def __init__(self,ecd_upper_threshold_delta=1.5,max_spp_limit=3500.0): self.ecd_threshold_delta=ecd_upper_threshold_delta; self.max_spp=max_spp_limit
    def analyze_telemetry(self,physics_metrics,pore_limit,frac_limit,baseline_esd_ppg=None,historical_esd=None):
        if pore_limit is None or frac_limit is None: raise ValueError("Pore-pressure and fracture-gradient limits are required.")
        ecd=physics_metrics.get("ecd_ppg",0.0); spp=physics_metrics.get("standpipe_pressure_psi")
        base=baseline_esd_ppg if baseline_esd_ppg is not None else historical_esd
        if base is None: base=physics_metrics.get("surface_mud_weight_ppg",0.0)
        delta=ecd-base; flags=[]; severity="GREEN"; hazard="None"; rec=[]
        if ecd<pore_limit: severity="RED"; hazard="Underbalanced / Kick Risk"; flags.append(f"ECD ({ecd:.2f} ppg) below pore pressure ({pore_limit:.2f} ppg)."); rec.append("Review mud density and operating conditions against the approved well-control programme.")
        elif ecd>frac_limit: severity="RED"; hazard="Formation Fracture / Severe Losses"; flags.append(f"ECD ({ecd:.2f} ppg) exceeds fracture gradient ({frac_limit:.2f} ppg)."); rec.append("Review flow rate, rheology and mud density against the approved drilling programme.")
        elif delta>=self.ecd_threshold_delta: severity="YELLOW"; hazard="Excessive Annular Friction Spike"; flags.append(f"ECD increased by {delta:.2f} ppg over baseline."); rec.append("Investigate hole cleaning and circulating conditions.")
        elif delta>0.8: severity="YELLOW"; hazard="Moderate Friction Surge"; flags.append(f"ECD increased by {delta:.2f} ppg over baseline."); rec.append("Monitor cuttings loading and ECD trend.")
        if spp is not None and spp>self.max_spp: severity="RED"; hazard="Standpipe Pressure Excursion"; flags.append(f"Standpipe pressure ({spp:.1f} psi) exceeds configured limit ({self.max_spp:.1f} psi)."); rec.append("Review surface pressure and possible flow restrictions.")
        if not rec: rec.append("Hydraulic state remains within the configured screening limits.")
        return {"status":severity,"severity":severity,"delta_ecd_ppg":round(delta,2),"baseline_esd_ppg":round(base,2),"calculated_ecd_ppg":ecd,"standpipe_pressure_psi":spp,"flags":flags,"recommendation":rec[0],"pore_limit":round(pore_limit,2),"frac_limit":round(frac_limit,2),"matched_hazard":hazard,"detailed_diagnosis":" ".join(flags) if flags else f"Hydraulic state stable. Dynamic ECD is {ecd:.2f} ppg.","actionable_recommendations":rec,"annular_dp_status":"CALCULATED"}
