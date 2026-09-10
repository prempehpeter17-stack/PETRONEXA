"""
PetroNexa Test Suite - Input Validation & Non-Newtonian Physics Check
"""
import pytest
from source.physics import DrillingFluidEngine, WellSegment

def test_invalid_mud_weight_raises_error():
    with pytest.raises(ValueError, match="Invalid surface_mud_weight_ppg"):
        DrillingFluidEngine(
            surface_mud_weight_ppg=-5.0,
            flow_rate_gpm=400.0,
            total_depth_ft=10000.0,
            true_vertical_depth_ft=10000.0
        )

def test_tvd_exceeding_md_raises_error():
    with pytest.raises(ValueError, match="TVD .* cannot exceed Total Measured Depth"):
        DrillingFluidEngine(
            surface_mud_weight_ppg=10.0,
            flow_rate_gpm=400.0,
            total_depth_ft=8000.0,
            true_vertical_depth_ft=10000.0
        )

def test_generalized_reynolds_calculation():
    engine = DrillingFluidEngine(
        surface_mud_weight_ppg=12.0,
        flow_rate_gpm=500.0,
        total_depth_ft=12000.0,
        true_vertical_depth_ft=12000.0
    )
    
    # Power-law parameters: k = 300 eq cP, n = 0.65
    re_g = engine.calculate_generalized_reynolds(
        velocity_fps=4.5,
        hydraulic_diameter_in=2.0,
        mud_weight_ppg=12.0,
        k_consistency=300.0,
        n_index=0.65
    )
    assert re_g > 0
    assert isinstance(re_g, float)

def test_well_segment_invalid_geometry():
    with pytest.raises(ValueError, match="Inner diameter .* must be less than outer diameter"):
        WellSegment(length_ft=1000, inner_diameter_in=8.5, outer_diameter_in=6.0, mud_weight_ppg=10.0)
