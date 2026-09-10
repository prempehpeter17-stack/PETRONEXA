"""
Pore Pressure, Fracture Gradient, and Mud Weight Window Calculations.
"""
from typing import List, Dict, Any
from fastapi import HTTPException, status


def calculate_eaton_pore_pressure(
    overburden_gradient_ppg: float,
    normal_pore_pressure_ppg: float,
    observed_dt: float,
    normal_dt: float,
    eaton_exponent: float = 1.2,
) -> float:
    """Calculates pore pressure using Eaton's Sonic method."""
    if observed_dt <= 0 or normal_dt <= 0:
        raise ValueError("Sonic transit times (dt) must be strictly positive.")
    
    dt_ratio = (normal_dt / observed_dt) ** eaton_exponent
    pp_ppg = overburden_gradient_ppg - (overburden_gradient_ppg - normal_pore_pressure_ppg) * dt_ratio
    return round(pp_ppg, 2)


def calculate_hubbert_willis_frac_gradient(
    pore_pressure_ppg: float,
    overburden_gradient_ppg: float,
    poisson_ratio: float = 0.25,
) -> float:
    """Calculates formation fracture gradient via Hubbert & Willis relation."""
    k0 = poisson_ratio / (1.0 - poisson_ratio)
    fg_ppg = pore_pressure_ppg + k0 * (overburden_gradient_ppg - pore_pressure_ppg)
    return round(fg_ppg, 2)


def evaluate_pressure_window(
    depth_intervals: List[float],
    pore_pressures: List[float],
    frac_gradients: List[float],
    pp_safety_margin_ppg: float = 0.5,
    fg_safety_margin_ppg: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Evaluates operating mud weight windows across depth intervals with strict array-length verification
    and configurable safety margins.
    """
    if not (len(depth_intervals) == len(pore_pressures) == len(frac_gradients)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Array length mismatch: depth_intervals ({len(depth_intervals)}), "
                f"pore_pressures ({len(pore_pressures)}), frac_gradients ({len(frac_gradients)}). "
                "All input vectors must be of equal length."
            ),
        )

    window_data = []
    for depth, pp, fg in zip(depth_intervals, pore_pressures, frac_gradients):
        min_mw = pp + pp_safety_margin_ppg
        max_mw = fg - fg_safety_margin_ppg
        margin = max_mw - min_mw

        window_data.append({
            "depth_ft": depth,
            "pore_pressure_ppg": pp,
            "fracture_gradient_ppg": fg,
            "recommended_min_mw_ppg": round(min_mw, 2),
            "recommended_max_mw_ppg": round(max_mw, 2),
            "window_margin_ppg": round(margin, 2),
            "is_valid_window": margin > 0.0,
        })

    return window_data


class PressureGradientProfile:
    def __init__(self, depths: List[float], pore_pressures: List[float], frac_gradients: List[float]):
        if not (len(depths) == len(pore_pressures) == len(frac_gradients)):
            raise ValueError("All pressure profile vectors must have matching dimensions.")
        self.depths = depths
        self.pore_pressures = pore_pressures
        self.frac_gradients = frac_gradients

    def _interpolate(self, depth: float, values: List[float]) -> float:
        if depth <= self.depths[0]:
            return values[0]
        if depth >= self.depths[-1]:
            return values[-1]
        for i in range(len(self.depths) - 1):
            if self.depths[i] <= depth <= self.depths[i + 1]:
                d0, d1 = self.depths[i], self.depths[i + 1]
                v0, v1 = values[i], values[i + 1]
                return v0 + (v1 - v0) * ((depth - d0) / (d1 - d0))
        return values[0]

    def get_pore_at_depth(self, depth: float) -> float:
        return round(self._interpolate(depth, self.pore_pressures), 2)

    def get_frac_at_depth(self, depth: float) -> float:
        return round(self._interpolate(depth, self.frac_gradients), 2)
