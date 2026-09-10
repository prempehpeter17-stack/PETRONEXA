"""
PetroNexa API - Unified Main Entrypoint
"""
from fastapi import FastAPI, HTTPException, Status
from pydantic import BaseModel, Field
from typing import List, Optional
from source.physics import DrillingFluidEngine

app = FastAPI(
    title="PetroNexa API",
    version="1.0.0",
    description="Engineered Petroleum & Drilling Hydraulics API"
)

class WellSegmentSchema(BaseModel):
    length_ft: float = Field(..., gt=0, description="Segment length in feet")
    inner_diameter_in: float = Field(..., gt=0, description="Inner diameter in inches")
    outer_diameter_in: float = Field(..., gt=0, description="Outer diameter in inches")
    mud_weight_ppg: float = Field(..., gt=0, description="Mud weight in ppg")

class HydraulicsPayloadSchema(BaseModel):
    surface_mud_weight_ppg: float = Field(..., gt=0, description="Surface mud weight in ppg")
    flow_rate_gpm: float = Field(..., gt=0, description="Flow rate in GPM")
    total_depth_ft: float = Field(..., gt=0, description="Measured Depth in feet")
    true_vertical_depth_ft: float = Field(..., gt=0, description="True Vertical Depth in feet")
    equivalent_static_density_ppg: Optional[float] = Field(None, gt=0, description="ESD in ppg")
    segments: Optional[List[WellSegmentSchema]] = Field(default=[], description="Wellbore segments")
    
    # Configurable Safety Margins
    pp_safety_margin_ppg: float = Field(default=0.5, ge=0.0)
    fg_safety_margin_ppg: float = Field(default=0.2, ge=0.0)

@app.post("/api/v1/hydraulics/calculate", status_code=Status.HTTP_200_OK)
async def calculate_hydraulics(payload: HydraulicsPayloadSchema):
    esd_provided = payload.equivalent_static_density_ppg is not None
    esd_used = payload.equivalent_static_density_ppg if esd_provided else payload.surface_mud_weight_ppg
    
    diagnostic_warnings = []
    if not esd_provided:
        diagnostic_warnings.append("ESD not provided — surface mud weight used as baseline.")

    try:
        engine = DrillingFluidEngine(
            surface_mud_weight_ppg=payload.surface_mud_weight_ppg,
            flow_rate_gpm=payload.flow_rate_gpm,
            total_depth_ft=payload.total_depth_ft,
            true_vertical_depth_ft=payload.true_vertical_depth_ft
        )
        
        # Default mock pressure drop for response verification
        mock_annular_dp = 250.0  # psi
        ecd = engine.calculate_bottomhole_ecd(total_annular_dp_psi=mock_annular_dp)

        return {
            "status": "success",
            "esd_used_ppg": esd_used,
            "calculated_ecd_ppg": ecd,
            "diagnostics": {
                "warnings": diagnostic_warnings,
                "pp_safety_margin_ppg": payload.pp_safety_margin_ppg,
                "fg_safety_margin_ppg": payload.fg_safety_margin_ppg
            }
        }
    except ValueError as err:
        raise HTTPException(status_code=Status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))
