"""Reservoir Engineering v1 calculation engine for PetroNexa.

Field-unit correlations are explicit and inputs are validated. Results are
decision-support calculations and should be checked against field data.
"""
import math
from typing import Dict, Any

class ReservoirEngineeringEngine:
    @staticmethod
    def _positive(name,v):
        if v <= 0: raise ValueError(f"{name} must be greater than zero.")
    @staticmethod
    def properties(bulk_volume_acft: float, net_to_gross: float, porosity: float, water_saturation: float,
                   permeability_md: float, rock_compressibility_psi: float=0.0, water_compressibility_psi: float=0.0):
        ReservoirEngineeringEngine._positive("Bulk rock volume",bulk_volume_acft); ReservoirEngineeringEngine._positive("Permeability",permeability_md)
        for n,v in (("Net-to-gross",net_to_gross),("Porosity",porosity),("Water saturation",water_saturation)):
            if not 0 < v <= 1: raise ValueError(f"{n} must be between 0 and 1.")
        hydrocarbon_saturation=1-water_saturation; net_rock_volume=bulk_volume_acft*net_to_gross; pore_volume=net_rock_volume*porosity; hydrocarbon_pore_volume=pore_volume*hydrocarbon_saturation
        return {"bulk_rock_volume_acft":bulk_volume_acft,"net_rock_volume_acft":net_rock_volume,"porosity_fraction":porosity,"water_saturation_fraction":water_saturation,"hydrocarbon_saturation_fraction":hydrocarbon_saturation,"pore_volume_acft":pore_volume,"hydrocarbon_pore_volume_acft":hydrocarbon_pore_volume,"permeability_md":permeability_md,"rock_compressibility_1_psi":rock_compressibility_psi,"water_compressibility_1_psi":water_compressibility_psi}
    @staticmethod
    def darcy_rate(permeability_md:float, thickness_ft:float, pressure_drop_psi:float, viscosity_cp:float, formation_volume_factor_rb_stb:float, length_ft:float):
        for n,v in (("Permeability",permeability_md),("Thickness",thickness_ft),("Viscosity",viscosity_cp),("Formation volume factor",formation_volume_factor_rb_stb),("Flow length",length_ft)): ReservoirEngineeringEngine._positive(n,v)
        if pressure_drop_psi <= 0: raise ValueError("Pressure drop must be greater than zero.")
        q=0.001127*permeability_md*thickness_ft*pressure_drop_psi/(viscosity_cp*formation_volume_factor_rb_stb*length_ft)
        return {"oil_rate_stb_day":q,"pressure_drop_psi":pressure_drop_psi}
    @staticmethod
    def radial_flow(permeability_md:float, thickness_ft:float, reservoir_pressure_psi:float, bottomhole_pressure_psi:float, viscosity_cp:float, formation_volume_factor_rb_stb:float, drainage_radius_ft:float, wellbore_radius_ft:float, skin:float=0.0):
        for n,v in (("Permeability",permeability_md),("Thickness",thickness_ft),("Viscosity",viscosity_cp),("Formation volume factor",formation_volume_factor_rb_stb),("Drainage radius",drainage_radius_ft),("Wellbore radius",wellbore_radius_ft)): ReservoirEngineeringEngine._positive(n,v)
        if reservoir_pressure_psi <= bottomhole_pressure_psi: raise ValueError("Reservoir pressure must exceed bottomhole pressure.")
        if drainage_radius_ft <= wellbore_radius_ft: raise ValueError("Drainage radius must exceed wellbore radius.")
        denom=141.2*viscosity_cp*formation_volume_factor_rb_stb*(math.log(drainage_radius_ft/wellbore_radius_ft)-0.75+skin)
        if denom <= 0: raise ValueError("Flow denominator is non-positive; check radius and skin.")
        q=permeability_md*thickness_ft*(reservoir_pressure_psi-bottomhole_pressure_psi)/denom
        return {"oil_rate_stb_day":q,"productivity_index_stb_day_psi":q/(reservoir_pressure_psi-bottomhole_pressure_psi),"flow_pressure_drop_psi":reservoir_pressure_psi-bottomhole_pressure_psi}
    @staticmethod
    def material_balance(numerator_F:float, water_influx_rb:float, oil_expansion_Eo_rb_stb:float, gas_cap_ratio_m:float=0.0, gas_cap_expansion_Eg_rb_stb:float=0.0, formation_water_expansion_Efw_rb_stb:float=0.0):
        denom=oil_expansion_Eo_rb_stb+gas_cap_ratio_m*gas_cap_expansion_Eg_rb_stb+formation_water_expansion_Efw_rb_stb
        if denom <= 0: raise ValueError("Total expansion term must be greater than zero.")
        N=(numerator_F-water_influx_rb)/denom
        return {"original_oil_in_place_stb":N,"underground_withdrawal_F_rb":numerator_F,"water_influx_rb":water_influx_rb,"total_expansion_rb_stb":denom}
    @staticmethod
    def vogel_ipr(reservoir_pressure_psi:float, test_rate_stb_day:float, test_bhp_psi:float, target_bhp_psi:float):
        if reservoir_pressure_psi<=0 or test_rate_stb_day<=0: raise ValueError("Reservoir pressure and test rate must be positive.")
        if not 0<=test_bhp_psi<reservoir_pressure_psi: raise ValueError("Test bottomhole pressure must be below reservoir pressure and non-negative.")
        if not 0<=target_bhp_psi<reservoir_pressure_psi: raise ValueError("Target bottomhole pressure must be below reservoir pressure and non-negative.")
        x=test_bhp_psi/reservoir_pressure_psi; qmax=test_rate_stb_day/(1-0.2*x-0.8*x*x)
        xt=target_bhp_psi/reservoir_pressure_psi; qtarget=qmax*(1-0.2*xt-0.8*xt*xt)
        return {"maximum_oil_rate_stb_day":qmax,"target_oil_rate_stb_day":qtarget,"target_bhp_psi":target_bhp_psi}
    @staticmethod
    def productivity_index(test_rate_stb_day:float,reservoir_pressure_psi:float,bottomhole_pressure_psi:float):
        drawdown=reservoir_pressure_psi-bottomhole_pressure_psi
        if test_rate_stb_day<=0 or drawdown<=0: raise ValueError("Rate and drawdown must be positive.")
        return {"productivity_index_stb_day_psi":test_rate_stb_day/drawdown,"drawdown_psi":drawdown}
