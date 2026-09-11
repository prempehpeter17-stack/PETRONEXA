"""PetroNexa FastAPI backend.

The API exposes the existing validated engineering engines to mobile, desktop,
and web clients. Engineering calculations remain in pure-Python modules so they
can be tested independently from the UI.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from physics import DrillingHydraulicsEngine, WellSegment, DiagnosticEngine
from cementing_engine import PrimaryCementingInput, CementingEngine
from pdf_generator import generate_pdf_payload
from database import init_db, get_db, UserModel, Project
from auth import get_current_user
from router import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("petronexa.api")
ai_diagnostics: Optional[DiagnosticEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PetroNexa services...")
    await init_db()
    global ai_diagnostics
    ai_diagnostics = DiagnosticEngine(ecd_upper_threshold_delta=1.5, max_spp_limit=3500.0)
    yield
    logger.info("PetroNexa services stopped.")

app = FastAPI(
    title="PetroNexa API",
    description="Petroleum Engineering Intelligence Platform API.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
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
    surface_mud_weight_ppg: float = Field(default=10.0, gt=0.0)
    plastic_viscosity_cp: float = Field(default=20.0, ge=0.0)
    yield_point_lb_100ft2: float = Field(default=15.0, ge=0.0)
    segments: Optional[List[WellSegmentSchema]] = None

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    well_name: str = Field(default="", max_length=120)
    field_name: str = Field(default="", max_length=120)
    rig_name: str = Field(default="", max_length=120)
    trajectory_data: dict | None = None

@app.get("/", tags=["System Status"])
async def root():
    return {"system": settings.app_name, "status": "OPERATIONAL", "version": settings.app_version}

@app.get("/health", tags=["System Status"])
async def health():
    return {"status": "ok", "service": "petronexa-api", "version": settings.app_version}

@app.get("/api/v1/me", tags=["Authentication"])
async def me(current_user: UserModel = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "company_name": current_user.company_name,
    }

@app.get("/api/v1/projects", tags=["Projects"])
async def list_projects(current_user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc()))
    return [
        {
            "id": p.id,
            "name": p.name,
            "well_name": p.well_name,
            "field_name": p.field_name,
            "rig_name": p.rig_name,
            "created_at": p.created_at,
        }
        for p in result.scalars().all()
    ]

@app.post("/api/v1/projects", status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(payload: ProjectCreate, current_user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = Project(user_id=current_user.id, **payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return {"id": project.id, **payload.model_dump()}

@app.post("/api/v1/hydraulics/calculate", tags=["Hydraulics Engine"])
async def calculate_hydraulics(payload: HydraulicsPayloadSchema, current_user: UserModel = Depends(get_current_user)):
    try:
        engine = DrillingHydraulicsEngine(
            surface_mud_weight_ppg=payload.surface_mud_weight_ppg,
            flow_rate_gpm=payload.flow_rate_gpm,
            total_depth_ft=payload.total_depth_ft,
            plastic_viscosity_cp=payload.plastic_viscosity_cp,
            yield_point_lb_100ft2=payload.yield_point_lb_100ft2,
        )
        if payload.segments:
            for seg in payload.segments:
                if seg.bottom_md <= seg.top_md:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid segment geometry in '{seg.name}': bottom MD must exceed top MD.",
                    )
                if seg.bottom_md > payload.total_depth_ft:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid segment geometry in '{seg.name}': bottom MD cannot exceed Total Depth.",
                    )

                segment_length = seg.bottom_md - seg.top_md
                engine.add_segment(
                    WellSegment(
                        name=seg.name,
                        length_ft=segment_length,
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
        diagnostics = ai_diagnostics.analyze_telemetry(physics_metrics=results, historical_esd=payload.surface_mud_weight_ppg) if ai_diagnostics else {}
        return {"physics_results": results, "diagnostics": diagnostics}

    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        logger.exception("Hydraulics calculation engine internal failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hydraulics calculation failed due to an internal server error. Please review your input parameters.",
        )

@app.post("/api/v1/hydraulics/export-pdf", tags=["Reports"])
async def export_pdf_report(payload: HydraulicsPayloadSchema, current_user: UserModel = Depends(get_current_user)):
    try:
        calc_response = await calculate_hydraulics(payload, current_user)
        pdf_buffer = generate_pdf_payload(
            project_metadata={
                "name": payload.segments[0].name if payload.segments else "Default Well",
                "rig_name": "",
                "company": current_user.company_name,
            },
            physics_results=calc_response["physics_results"],
            diagnostic_results=calc_response["diagnostics"],
            engineer_name=current_user.username,
            cementing_results=None,
        )
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=PetroNexa_Technical_Report.pdf"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PDF report generation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate technical PDF report.",
        )

@app.post("/api/v1/cementing/design", tags=["Cementing Engine"])
async def design_cement_job(params: PrimaryCementingInput, current_user: UserModel = Depends(get_current_user)):
    try:
        return CementingEngine().design_primary_job(params)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        logger.exception("Cementing calculation engine failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cementing job design failed due to an internal calculation error.",
        )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
