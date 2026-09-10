"""
PetroNexa Main API Application Core.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from physics import DrillingHydraulicsEngine, WellSegment, DiagnosticEngine, RheologyModel
from cementing_engine import PrimaryCementingInput, CementingEngine
from gradients import evaluate_pressure_window
from pdf_generator import generate_pdf_payload
from database import init_db, get_db, UserModel, Base
from auth import get_current_user
from router import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("petronexa.api")
ai_diagnostics: Optional[DiagnosticEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PetroNexa backend services...")
    await init_db()
    global ai_diagnostics
    ai_diagnostics = DiagnosticEngine(ecd_upper_threshold_delta=1.5, max_spp_limit=3500.0)
    yield
    logger.info("PetroNexa backend shut down.")


app = FastAPI(
    title=settings.app_name,
    description="Production-grade API for wellbore hydraulics, cementing, and geomechanics.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)


class WellSegmentSchema(BaseModel):
    name: str = Field(default="Drill Pipe", max_length=100)
    top_md: float = Field(default=0.0, ge=0.0)
    bottom_md: float = Field(default=7000.0, ge=0.0)
    pipe_od: float = Field(default=5.0, gt=0.0)
    pipe_id: float = Field(default=4.276, gt=0.0)
    hole_id: float = Field(default=8.5, gt=0.0)


class HydraulicsPayloadSchema(BaseModel):
    flow_rate_gpm: float = Field(default=450.0, gt=0.0)
    total_depth_ft: float = Field(default=8000.0, gt=0.0)
    true_vertical_depth_ft: Optional[float] = Field(default=None, gt=0.0)
    surface_mud_weight_ppg: float = Field(default=10.0, gt=0.0)
    equivalent_static_density_ppg: Optional[float] = Field(default=None, gt=0.0)
    plastic_viscosity_cp: float = Field(default=20.0, ge=0.0)
    yield_point_lb_100ft2: float = Field(default=15.0, ge=0.0)
    rheology_model: RheologyModel = Field(default=RheologyModel.BINGHAM_PLASTIC)
    segments: Optional[List[WellSegmentSchema]] = None


class PressureWindowPayloadSchema(BaseModel):
    depth_intervals: List[float]
    pore_pressures: List[float]
    frac_gradients: List[float]
    pp_safety_margin_ppg: float = Field(default=0.5, ge=0.0)
    fg_safety_margin_ppg: float = Field(default=0.2, ge=0.0)


@app.get("/health", tags=["System Status"])
async def health():
    return {"status": "ok", "service": "petronexa-api", "version": settings.app_version}


@app.post("/api/v1/hydraulics/calculate", tags=["Hydraulics Engine"])
async def calculate_hydraulics(
    payload: HydraulicsPayloadSchema,
    current_user: UserModel = Depends(get_current_user),
):
    try:
        tvd = payload.true_vertical_depth_ft if payload.true_vertical_depth_ft else payload.total_depth_ft
        esd = payload.equivalent_static_density_ppg if payload.equivalent_static_density_ppg else payload.surface_mud_weight_ppg

        engine = DrillingHydraulicsEngine(
            surface_mud_weight_ppg=payload.surface_mud_weight_ppg,
            flow_rate_gpm=payload.flow_rate_gpm,
            total_depth_ft=payload.total_depth_ft,
            true_vertical_depth_ft=tvd,
            plastic_viscosity_cp=payload.plastic_viscosity_cp,
            yield_point_lb_100ft2=payload.yield_point_lb_100ft2,
            rheology_model=payload.rheology_model,
        )

        if payload.segments:
            for seg in payload.segments:
                length = max(0.0, seg.bottom_md - seg.top_md)
                engine.add_segment(
                    WellSegment(
                        name=seg.name,
                        length_ft=length,
                        pipe_od_in=seg.pipe_od,
                        pipe_id_in=seg.pipe_id,
                        hole_id_in=seg.hole_id,
                        mud_weight_ppg=payload.surface_mud_weight_ppg,
                        viscosity_cp=payload.plastic_viscosity_cp,
                        yield_point_lb_100ft2=payload.yield_point_lb_100ft2,
                    )
                )
        else:
            engine.add_segment(
                WellSegment(
                    name="Default Drill String",
                    length_ft=payload.total_depth_ft,
                    pipe_od_in=5.0,
                    pipe_id_in=4.276,
                    hole_id_in=8.5,
                    mud_weight_ppg=payload.surface_mud_weight_ppg,
                    viscosity_cp=payload.plastic_viscosity_cp,
                    yield_point_lb_100ft2=payload.yield_point_lb_100ft2,
                )
            )

        results = engine.solve()
        diagnostics = ai_diagnostics.analyze_telemetry(
            physics_metrics=results, equivalent_static_density_esd=esd
        ) if ai_diagnostics else {}

        return {"physics_results": results, "diagnostics": diagnostics}
    except Exception as exc:
        logger.exception("Hydraulics calculation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation Engine Failure: {exc}",
        )


@app.post("/api/v1/hydraulics/export-pdf", tags=["Reports"])
async def export_pdf_report(
    payload: HydraulicsPayloadSchema,
    current_user: UserModel = Depends(get_current_user),
):
    calc_response = await calculate_hydraulics(payload, current_user)
    pdf_buffer = generate_pdf_payload(
        project_metadata={
            "name": payload.segments[0].name if payload.segments else "Default Well",
            "field_name": "Active Field",
            "rig_name": "Rig 1",
            "company": current_user.company_name or "PetroNexa",
        },
        physics_results=calc_response["physics_results"],
        diagnostic_results=calc_response["diagnostics"],
        engineer_name=current_user.username,
    )
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=PetroNexa_Technical_Report.pdf"},
    )


@app.post("/api/v1/cementing/design", tags=["Cementing Engine"])
async def design_cement_job(
    params: PrimaryCementingInput,
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return CementingEngine().design_primary_job(params)
    except Exception as exc:
        logger.exception("Cementing calculation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cementing Engine Failure: {exc}",
        )


@app.post("/api/v1/geomechanics/window", tags=["Geomechanics Engine"])
async def calculate_mud_window(
    payload: PressureWindowPayloadSchema,
    current_user: UserModel = Depends(get_current_user),
):
    return evaluate_pressure_window(
        depth_intervals=payload.depth_intervals,
        pore_pressures=payload.pore_pressures,
        frac_gradients=payload.frac_gradients,
        pp_safety_margin_ppg=payload.pp_safety_margin_ppg,
        fg_safety_margin_ppg=payload.fg_safety_margin_ppg,
    )
