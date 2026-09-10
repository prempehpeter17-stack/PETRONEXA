"""
PetroNexa Engineering Engine - Cementing Operations Module
"""
import math
from typing import List, Dict

class CementingEngine:
    def __init__(
        self,
        casing_outer_diameter_in: float,
        casing_inner_diameter_in: float,
        hole_diameter_in: float,
        total_depth_ft: float,
        top_of_cement_ft: float
    ):
        if casing_outer_diameter_in <= 0 or casing_inner_diameter_in <= 0 or hole_diameter_in <= 0:
            raise ValueError("All diameter inputs must be strictly greater than zero.")
        if casing_inner_diameter_in >= casing_outer_diameter_in:
            raise ValueError("Casing inner diameter must be less than outer diameter.")
        if casing_outer_diameter_in >= hole_diameter_in:
            raise ValueError("Casing outer diameter must be smaller than wellbore hole diameter.")
        if total_depth_ft <= 0 or top_of_cement_ft < 0:
            raise ValueError("Well depths must be non-negative values.")
        if top_of_cement_ft >= total_depth_ft:
            raise ValueError("Top of cement (TOC) must be shallower than Total Depth (TD).")

        self.casing_od = casing_outer_diameter_in
        self.casing_id = casing_inner_diameter_in
        self.hole_diameter = hole_diameter_in
        self.total_depth_ft = total_depth_ft
        self.top_of_cement_ft = top_of_cement_ft

    def calculate_annular_capacity_bbl_ft(self) -> float:
        """Calculates annular capacity between casing OD and open hole diameter in bbl/ft."""
        capacity = (self.hole_diameter**2 - self.casing_od**2) / 1029.4
        return round(capacity, 5)

    def calculate_slurry_volume_bbl(self, excess_percentage: float = 0.0) -> float:
        """Calculates total required cement slurry volume including excess factor."""
        if excess_percentage < 0:
            raise ValueError("Excess percentage cannot be negative.")

        cement_interval_ft = self.total_depth_ft - self.top_of_cement_ft
        net_capacity = self.calculate_annular_capacity_bbl_ft()
        base_volume = cement_interval_ft * net_capacity
        total_volume = base_volume * (1.0 + (excess_percentage / 100.0))
        return round(total_volume, 2)

    def calculate_displacement_volume_bbl(self, shoe_track_length_ft: float = 0.0) -> float:
        """Calculates displacement fluid volume to bump plug, accounting for shoe track."""
        if shoe_track_length_ft < 0 or shoe_track_length_ft >= self.total_depth_ft:
            raise ValueError("Invalid shoe track length.")

        displacement_depth = self.total_depth_ft - shoe_track_length_ft
        internal_capacity_bbl_ft = (self.casing_id**2) / 1029.4
        displacement_vol = displacement_depth * internal_capacity_bbl_ft
        return round(displacement_vol, 2)

    def calculate_hydrostatic_head_psi(
        self, 
        slurry_density_ppg: float, 
        mud_density_ppg: float
    ) -> Dict[str, float]:
        """Calculates final bottomhole hydrostatic pressure post-cement placement."""
        if slurry_density_ppg <= 0 or mud_density_ppg <= 0:
            raise ValueError("Fluid densities must be positive non-zero values.")

        cement_height_ft = self.total_depth_ft - self.top_of_cement_ft
        mud_height_ft = self.top_of_cement_ft

        p_cement = 0.052 * slurry_density_ppg * cement_height_ft
        p_mud = 0.052 * mud_density_ppg * mud_height_ft
        total_bhp_psi = p_cement + p_mud

        return {
            "cement_hydrostatic_psi": round(p_cement, 2),
            "mud_hydrostatic_psi": round(p_mud, 2),
            "total_bottomhole_pressure_psi": round(total_bhp_psi, 2)
        }
