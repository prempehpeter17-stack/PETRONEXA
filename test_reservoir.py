import math
from reservoir import ReservoirEngineeringEngine as R

def test_reservoir_properties():
    r = R.properties(100, 0.8, 0.2, 0.3, 100)
    assert math.isclose(r['net_rock_volume_acft'], 80.0)
    assert math.isclose(r['hydrocarbon_pore_volume_acft'], 11.2)

def test_darcy_rate_positive():
    r = R.darcy_rate(100, 50, 500, 2, 1.2, 1000)
    assert r['oil_rate_stb_day'] > 0

def test_radial_flow_and_pi():
    r = R.radial_flow(100, 50, 3500, 2500, 2, 1.2, 2000, 0.35)
    assert r['oil_rate_stb_day'] > 0
    assert math.isclose(r['productivity_index_stb_day_psi'], r['oil_rate_stb_day']/1000)

def test_material_balance():
    r = R.material_balance(500000, 100000, 2.0, 0.5, 1.5, 0.2)
    assert r['original_oil_in_place_stb'] > 0

def test_vogel_ipr():
    r = R.vogel_ipr(3000, 500, 1800, 1500)
    assert r['maximum_oil_rate_stb_day'] > r['target_oil_rate_stb_day'] > 0

def test_productivity_index():
    r = R.productivity_index(500, 3000, 2500)
    assert math.isclose(r['productivity_index_stb_day_psi'], 1.0)
