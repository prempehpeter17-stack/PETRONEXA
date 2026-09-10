"""
Volumetric Reference Comparison Engine.
Provides geometric base-case comparison against detailed multi-string calculations.
"""
from typing import Dict, Any


def compare_cementing_theoretical_volume(
    calculated_results: Dict[str, Any],
    casing_od_in: float,
    hole_dia_in: float,
    interval_length_ft: float,
) -> Dict[str, Any]:
    """
    Computes a simplified geometric annular reference volume for verification.
    Note: This is a geometric baseline and does not represent full job execution validation.
    """
    if hole_dia_in <= casing_od_in:
        raise ValueError("Hole diameter must be strictly greater than casing outer diameter.")

    base_annular_capacity_bbl_per_ft = (hole_dia_in**2 - casing_od_in**2) / 1029.4
    reference_vol_bbl = base_annular_capacity_bbl_per_ft * interval_length_ft

    calc_tail = calculated_results.get("tail_slurry_volume_bbl", 0.0)
    calc_lead = calculated_results.get("lead_slurry_volume_bbl", 0.0)
    total_calc_slurry = calc_tail + calc_lead

    variance_pct = 0.0
    if reference_vol_bbl > 0:
        variance_pct = ((total_calc_slurry - reference_vol_bbl) / reference_vol_bbl) * 100.0

    return {
        "theoretical_base_volume_bbl": round(reference_vol_bbl, 2),
        "calculated_total_slurry_bbl": round(total_calc_slurry, 2),
        "volume_variance_pct": round(variance_pct, 2),
        "comparison_note": (
            "Variance accounts for hole washout factors, shoe track capacities, and lead/tail splits."
        ),
    }
