
import math
from typing import Any, Dict


class ReservoirEngineeringEngine:
    """Basic reservoir engineering calculation engine for PetroNexa."""

    @staticmethod
    def _positive(value: float, name: str) -> float:
        value = float(value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive, finite number.")
        return value

    @staticmethod
    def properties(
        bulk_rock_volume_acre_ft: float,
        net_to_gross: float,
        porosity: float,
        water_saturation: float,
        permeability_md: float,
        rock_compressibility_per_psi: float,
        water_compressibility_per_psi: float,
    ) -> Dict[str, Any]:
        """Calculate basic reservoir rock and pore-volume properties."""

        values = {
            "Bulk rock volume": bulk_rock_volume_acre_ft,
            "Net-to-gross": net_to_gross,
            "Porosity": porosity,
            "Water saturation": water_saturation,
            "Permeability": permeability_md,
            "Rock compressibility": rock_compressibility_per_psi,
            "Water compressibility": water_compressibility_per_psi,
        }

        for name, value in values.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite number.")

        if bulk_rock_volume_acre_ft <= 0:
            raise ValueError("Bulk rock volume must be greater than zero.")
        if not 0 < net_to_gross <= 1:
            raise ValueError("Net-to-gross must be greater than 0 and at most 1.")
        if not 0 < porosity <= 1:
            raise ValueError("Porosity must be greater than 0 and at most 1.")
        if not 0 <= water_saturation <= 1:
            raise ValueError("Water saturation must be between 0 and 1.")
        if permeability_md < 0:
            raise ValueError("Permeability cannot be negative.")
        if rock_compressibility_per_psi < 0 or water_compressibility_per_psi < 0:
            raise ValueError("Compressibilities cannot be negative.")

        net_rock_volume = bulk_rock_volume_acre_ft * net_to_gross
        pore_volume_acre_ft = net_rock_volume * porosity
        pore_volume_rb = pore_volume_acre_ft * 7758.0
        hydrocarbon_pore_volume_rb = pore_volume_rb * (1.0 - water_saturation)

        return {
            "bulk_rock_volume_acre_ft": bulk_rock_volume_acre_ft,
            "net_to_gross": net_to_gross,
            "net_rock_volume_acre_ft": net_rock_volume,
            "porosity_fraction": porosity,
            "porosity_percent": porosity * 100.0,
            "water_saturation_fraction": water_saturation,
            "water_saturation_percent": water_saturation * 100.0,
            "permeability_md": permeability_md,
            "pore_volume_acre_ft": pore_volume_acre_ft,
            "pore_volume_rb": pore_volume_rb,
            "hydrocarbon_pore_volume_rb": hydrocarbon_pore_volume_rb,
            "rock_compressibility_per_psi": rock_compressibility_per_psi,
            "water_compressibility_per_psi": water_compressibility_per_psi,
        }

    @staticmethod
    def darcy_rate(
        permeability_md: float,
        area_ft2: float,
        pressure_drop_psi: float,
        viscosity_cp: float,
        length_ft: float,
    ) -> Dict[str, float]:
        """Single-phase linear Darcy flow; rate is in reservoir bbl/day."""
        k = ReservoirEngineeringEngine._positive(
            permeability_md, "Permeability"
        )
        area = ReservoirEngineeringEngine._positive(area_ft2, "Area")
        mu = ReservoirEngineeringEngine._positive(
            viscosity_cp, "Viscosity"
        )
        length = ReservoirEngineeringEngine._positive(length_ft, "Length")
        dp = float(pressure_drop_psi)

        if not math.isfinite(dp):
            raise ValueError("Pressure drop must be finite.")

        rate = 0.001127 * k * area * dp / (mu * length)

        return {
            "rate_rb_per_day": rate,
            "rate_magnitude_rb_per_day": abs(rate),
            "flow_direction": (
                "forward" if rate > 0 else
                "reverse" if rate < 0 else "no flow"
            ),
        }

    @staticmethod
    def radial_flow(
        permeability_md: float,
        thickness_ft: float,
        pressure_difference_psi: float,
        viscosity_cp: float,
        formation_volume_factor: float,
        drainage_radius_ft: float,
        wellbore_radius_ft: float,
        skin: float = 0.0,
    ) -> Dict[str, float]:
        """Approximate steady-state radial oil flow in reservoir bbl/day."""
        k = ReservoirEngineeringEngine._positive(
            permeability_md, "Permeability"
        )
        h = ReservoirEngineeringEngine._positive(thickness_ft, "Thickness")
        mu = ReservoirEngineeringEngine._positive(
            viscosity_cp, "Viscosity"
        )
        bo = ReservoirEngineeringEngine._positive(
            formation_volume_factor, "Formation volume factor"
        )
        re = ReservoirEngineeringEngine._positive(
            drainage_radius_ft, "Drainage radius"
        )
        rw = ReservoirEngineeringEngine._positive(
            wellbore_radius_ft, "Wellbore radius"
        )
        dp = float(pressure_difference_psi)
        skin = float(skin)

        if re <= rw:
            raise ValueError(
                "Drainage radius must exceed wellbore radius."
            )
        if not math.isfinite(dp) or not math.isfinite(skin):
            raise ValueError("Pressure difference and skin must be finite.")

        denominator = math.log(re / rw) + skin
        if denominator <= 0:
            raise ValueError(
                "The radial-flow denominator must be positive."
            )

        rate = 0.00708 * k * h * dp / (mu * bo * denominator)

        return {
            "rate_stb_per_day": rate,
            "rate_magnitude_stb_per_day": abs(rate),
            "flow_direction": (
                "production" if rate > 0 else
                "injection" if rate < 0 else "no flow"
            ),
            "productivity_index_stb_day_psi": (
                abs(rate / dp) if dp != 0 else 0.0
            ),
        }

    @staticmethod
    def material_balance(
        reservoir_volume_rb: float,
        oil_formation_volume_factor: float,
        initial_oil_formation_volume_factor: float,
        water_influx_rb: float = 0.0,
        gas_cap_ratio: float = 0.0,
        pressure_drop_psi: float = 0.0,
        compressibility_per_psi: float = 0.0,
    ) -> Dict[str, float]:
        """Simple tank-model estimate; not a full reservoir simulator."""
        n = ReservoirEngineeringEngine._positive(
            reservoir_volume_rb, "Reservoir volume"
        )
        bo = ReservoirEngineeringEngine._positive(
            oil_formation_volume_factor, "Current Bo"
        )
        boi = ReservoirEngineeringEngine._positive(
            initial_oil_formation_volume_factor, "Initial Bo"
        )
        we = float(water_influx_rb)
        m = float(gas_cap_ratio)
        dp = float(pressure_drop_psi)
        ct = float(compressibility_per_psi)

        if any(not math.isfinite(v) for v in (we, m, dp, ct)):
            raise ValueError("Material-balance inputs must be finite.")
        if we < 0 or m < 0 or dp < 0 or ct < 0:
            raise ValueError(
                "Water influx, gas-cap ratio, pressure drop, and "
                "compressibility cannot be negative."
            )

        expansion = bo / boi - 1
        compressibility_term = ct * dp
        denominator = expansion + compressibility_term

        if denominator <= 0:
            raise ValueError(
                "The calculated material-balance denominator must be "
                "positive. Check the supplied pressure and PVT data."
            )

        estimated_oil_rb = (n + we) / denominator

        return {
            "expansion_term": expansion,
            "compressibility_term": compressibility_term,
            "water_influx_rb": we,
            "gas_cap_ratio": m,
            "estimated_oil_rb": estimated_oil_rb,
            "note": (
                "Simplified educational estimate. Validate the equation "
                "and input definitions with reservoir engineering data "
                "before using it for field decisions."
            ),
        }

    @staticmethod
    def vogel_ipr(
        reservoir_pressure_psi: float,
        flowing_pressure_psi: float,
        maximum_rate_stb_per_day: float,
    ) -> Dict[str, float]:
        """Estimate oil rate using Vogel's IPR for a solution-gas drive."""
        pr = ReservoirEngineeringEngine._positive(
            reservoir_pressure_psi, "Reservoir pressure"
        )
        pwf = float(flowing_pressure_psi)
        qmax = ReservoirEngineeringEngine._positive(
            maximum_rate_stb_per_day, "Maximum rate"
        )

        if not math.isfinite(pwf) or pwf < 0 or pwf > pr:
            raise ValueError(
                "Flowing pressure must be between zero and reservoir pressure."
            )

        ratio = pwf / pr
        rate = qmax * (1 - 0.2 * ratio - 0.8 * ratio ** 2)

        return {
            "oil_rate_stb_per_day": max(0.0, rate),
            "maximum_rate_stb_per_day": qmax,
            "pressure_ratio": ratio,
        }

    @staticmethod
    def productivity_index(
        rate_stb_per_day: float,
        reservoir_pressure_psi: float,
        flowing_pressure_psi: float,
    ) -> Dict[str, float]:
        """Calculate PI = oil rate / (Pr - Pwf)."""
        rate = float(rate_stb_per_day)
        pr = float(reservoir_pressure_psi)
        pwf = float(flowing_pressure_psi)

        if any(not math.isfinite(v) for v in (rate, pr, pwf)):
            raise ValueError("Inputs must be finite numbers.")
        if rate < 0:
            raise ValueError("Production rate cannot be negative.")
        if pr <= pwf:
            raise ValueError(
                "Reservoir pressure must exceed flowing pressure."
            )

        drawdown = pr - pwf
        return {
            "drawdown_psi": drawdown,
            "productivity_index_stb_day_psi": rate / drawdown,
        }
