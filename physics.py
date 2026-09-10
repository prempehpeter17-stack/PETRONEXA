"""
PetroNexa Engineering Engine - Physics & Hydraulics Module
"""
import math
from typing import List, Dict, Optional

class WellSegment:
    def __init__(self, length_ft: float, inner_diameter_in: float, outer_diameter_in: float, mud_weight_ppg: float):
        if length_ft <= 0:
            raise ValueError(f"Segment length must be positive. Received: {length_ft}")
        if inner_diameter_in <= 0 or outer_diameter_in <= 0:
            raise ValueError("Segment diameters must be positive non-zero values.")
        if inner_diameter_in >= outer_diameter_in:
            raise ValueError(f"Inner diameter ({inner_diameter_in}\") must be less than outer diameter ({outer_diameter_in}\").")
        if mud_weight_ppg <= 0:
            raise ValueError(f"Mud weight must be positive. Received: {mud_weight_ppg}")

        self.length_ft = length_ft
        self.inner_diameter_in = inner_diameter_in
        self.outer_diameter_in = outer_diameter_in
        self.mud_weight_ppg = mud_weight_ppg


class DrillingFluidEngine:
    def __init__(
        self,
        surface_mud_weight_ppg: float,
        flow_rate_gpm: float,
        total_depth_ft: float,
        true_vertical_depth_ft: float
    ):
        # Strict Engineering Assertions - Reject bad inputs instead of silent modification
        if surface_mud_weight_ppg <= 0:
            raise ValueError(f"Invalid surface_mud_weight_ppg: {surface_mud_weight_ppg}. Density must be > 0.")
        if flow_rate_gpm <= 0:
            raise ValueError(f"Invalid flow_rate_gpm: {flow_rate_gpm}. Flow rate must be > 0.")
        if total_depth_ft <= 0 or true_vertical_depth_ft <= 0:
            raise ValueError("Wellbore depth parameters must be positive non-zero values.")
        if true_vertical_depth_ft > total_depth_ft:
            raise ValueError(f"TVD ({true_vertical_depth_ft} ft) cannot exceed Total Measured Depth ({total_depth_ft} ft).")

        self.surface_mud_weight_ppg = surface_mud_weight_ppg
        self.flow_rate_gpm = flow_rate_gpm
        self.total_depth_ft = total_depth_ft
        self.true_vertical_depth_ft = true_vertical_depth_ft

    def calculate_generalized_reynolds(
        self, 
        velocity_fps: float, 
        hydraulic_diameter_in: float, 
        mud_weight_ppg: float, 
        k_consistency: float, 
        n_index: float,
        tau_0: float = 0.0
    ) -> float:
        """
        Calculates Generalized Reynolds Number (Re_g) for non-Newtonian fluids (Power Law & Herschel-Bulkley).
        """
        if velocity_fps <= 0 or hydraulic_diameter_in <= 0 or k_consistency <= 0 or n_index <= 0:
            raise ValueError("Velocity, hydraulic diameter, consistency index, and flow behavior index must be positive.")

        # Equivalent shear rate for annular geometry (sec^-1)
        shear_rate = ((2 * n_index + 1) / (3 * n_index)) * ((12.0 * velocity_fps) / hydraulic_diameter_in)
        
        # Effective viscosity in cP
        shear_stress_lb_100ft2 = tau_0 + (k_consistency * (shear_rate ** n_index))
        effective_viscosity_cp = (shear_stress_lb_100ft2 / shear_rate) * 511.0 if shear_rate > 0 else 1.0

        # Generalized Reynolds Number
        density_lb_gal = mud_weight_ppg
        re_gen = (928.0 * density_lb_gal * velocity_fps * hydraulic_diameter_in) / effective_viscosity_cp
        return re_gen

    def calculate_bottomhole_ecd(self, total_annular_dp_psi: float, segment_weighted_mw: Optional[float] = None) -> float:
        """
        Calculates Equivalent Circulating Density (ECD) at bottomhole using segment-weighted baseline density.
        """
        if total_annular_dp_psi < 0:
            raise ValueError("Annular pressure drop cannot be negative.")

        base_mw = segment_weighted_mw if segment_weighted_mw is not None else self.surface_mud_weight_ppg
        ecd = base_mw + (total_annular_dp_psi / (0.052 * self.true_vertical_depth_ft))
        return round(ecd, 3)
