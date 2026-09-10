"""
Main Application Entry Point – PetroNexa API
Provides REST endpoints for hydraulics, cementing, pressure gradients, and PDF generation.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, Base, engine
from auth import get_current_user, UserModel
from physics import DrillingHydraulicsEngine, WellSegment, NozzleInput, DiagnosticEngine, RheologyModel
from cementing_engine import CementingEngine, PrimaryCementingInput
from gradients import calculate_eaton_pore_pressure, calculate_hubbert_willis_frac_gradient, evaluate_pressure_window
from pdf_generator import generate_hydraulics_pdf_report

app = FastAPI(
    title="PetroNexa Engineering API",
    version="2.0.0",
    description="Production-grade API for drilling hydraulics, cementing design, and wellbore safety diagnostics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Initialize DB schemas asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "PetroNexa API", "version": "2.0.0"}


@app.post("/api/v1/hydraulics/calculate", tags=["Hydraulics"])
async def calculate_hydraulics(
    segments: List[WellSegment],
    nozzles: List[NozzleInput],
    surface_mud_weight_ppg: float,
    flow_rate_gpm: float,
    total_depth_ft: float,
    true_vertical_depth_ft: float,
    rheology_model: RheologyModel = RheologyModel.BINGHAM_PLASTIC,
    plastic_viscosity_cp: float = 20.0,
    yield_point_lb_100ft2: float = 15.0,
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """Evaluates wellbore pressure losses, local segment ECDs, and bit hydraulics."""
    engine_inst = DrillingHydraulicsEngine(
        surface_mud_weight_ppg=surface_mud_weight_ppg,
        flow_rate_gpm=flow_rate_gpm,
        total_depth_ft=total_depth_ft,
        true_vertical_depth_ft=true_vertical_depth_ft,
        plastic_viscosity_cp=plastic_viscosity_cp,
        yield_point_lb_100ft2=yield_point_lb_100ft2,
        rheology_model=rheology_model,
    )

    for seg in segments:
        engine_inst.add_segment(seg)
    for n in nozzles:
        engine_inst.add_nozzle(n)

    results = engine_inst.solve()
    
    # Run diagnostic checks against telemetry limits
    diag = DiagnosticEngine()
    diagnostics = diag.analyze_telemetry(results, historical_esd=surface_mud_weight_ppg)
    results["diagnostics"] = diagnostics

    return results


@app.post("/api/v1/hydraulics/report/pdf", tags=["Hydraulics"])
async def export_hydraulics_pdf(
    hydraulics_results: Dict[str, Any],
    current_user: UserModel = Depends(get_current_user),
):
    """Generates a downloadable PDF report for a completed hydraulics evaluation."""
    pdf_buffer = generate_hydraulics_pdf_report(hydraulics_results)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=PetroNexa_Hydraulics_Report.pdf"},
    )


@app.post("/api/v1/cementing/design", tags=["Cementing"])
async def design_cement_job(
    params: PrimaryCementingInput,
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """Calculates displacement volumes, differential hydrostatic head, and plug bumping pressures."""
    c_engine = CementingEngine()
    results = c_engine.design_primary_job(params)
    return results


@app.post("/api/v1/geomechanics/window", tags=["Geomechanics"])
async def calculate_mud_window(
    depth_intervals: List[float],
    pore_pressures: List[float],
    frac_gradients: List[float],
    current_user: UserModel = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Evaluates safe operating drilling fluid weight windows across multiple depths."""
    return evaluate_pressure_window(depth_intervals, pore_pressures, frac_gradients)
