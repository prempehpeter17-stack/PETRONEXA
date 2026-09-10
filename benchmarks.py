"""
Industry benchmark comparative module for verifying PetroNexa against reference data.
"""
from typing import Dict, Any


def compare_cementing_results(
    calculated_results: Dict[str, Any],
    casing_od_in: float,
    hole_dia_in: float,
    interval_length_ft: float,
) -> Dict[str, Any]:
    """Compares calculated cementing outcomes against baseline standard estimates."""
    # Rough volumetric benchmark baseline
    base_annular_capacity_bbl_per_ft = ((hole_dia_in ** 2 - casing_od_in ** 2) / 1029.4)
    expected_vol_bbl = base_annular_capacity_bbl_per_ft * interval_length_ft

    calc_tail = calculated_results.get("tail_slurry_volume_bbl", 0.0)
    calc_lead = calculated_results.get("lead_slurry_volume_bbl", 0.0)
    total_calc_slurry = calc_tail + calc_lead

    variance_pct = 0.0
    if expected_vol_bbl > 0:
        variance_pct = ((total_calc_slurry - expected_vol_bbl) / expected_vol_bbl) * 100.0

    return {
        "benchmark_base_volume_bbl": round(expected_vol_bbl, 2),
        "calculated_total_slurry_bbl": round(total_calc_slurry, 2),
        "volume_variance_pct": round(variance_pct, 2),
        "pass_benchmarking": abs(variance_pct) <= 20.0,  # Within 20% considering washout/shoe track
    }
