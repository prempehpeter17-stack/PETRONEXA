"""
Pore Pressure & Fracture Gradient Calculations.
"""
from typing import Dict, List, Any


def calculate_eaton_pore_pressure(
    overburden_gradient_ppg: float,
    normal_pore_pressure_ppg: float,
    observed_dt: float,
    normal_dt: float,
    eaton_exponent: float = 1.2,
) -> float:
    """Calculates pore pressure via Eaton's Sonic Log method."""
    if observed_dt <= 0 or normal_dt <= 0:
        raise ValueError("Sonic transit times must be strictly positive.")
    
    dt_ratio = (normal_dt / observed_dt) ** eaton_exponent
    pp_ppg = overburden_gradient_ppg - (overburden_gradient_ppg - normal_pore_pressure_ppg) * dt_ratio
    return round(pp_ppg, 2)


def calculate_hubbert_willis_frac_gradient(
    pore_pressure_ppg: float,
    overburden_gradient_ppg: float,
    poisson_ratio: float = 0.25,
) -> float:
    """Calculates formation fracture gradient using Hubbert & Willis theory."""
    k0 = poisson_ratio / (1.0 - poisson_ratio)
    fg_ppg = pore_pressure_ppg + k0 * (overburden_gradient_ppg - pore_pressure_ppg)
    return round(fg_ppg, 2)


def evaluate_pressure_window(
    depth_intervals: List[float],
    pore_pressures: List[float],
    frac_gradients: List[float],
) -> List[Dict[str, Any]]:
    """Evaluates safe drilling mud weight windows across depth intervals."""
    window_data = []
    for depth, pp, fg in zip(depth_intervals, pore_pressures, frac_gradients):
        min_mw = pp + 0.5  # 0.5 ppg safety margin over pore pressure
        max_mw = fg - 0.2  # 0.2 ppg safety margin below fracture gradient
        window_data.append({
            "depth_ft": depth,
            "pore_pressure_ppg": pp,
            "fracture_gradient_ppg": fg,
            "recommended_min_mw_ppg": round(min_mw, 2),
            "recommended_max_mw_ppg": round(max_mw, 2),
            "window_margin_ppg": round(max_mw - min_mw, 2),
        })
    return window_data
