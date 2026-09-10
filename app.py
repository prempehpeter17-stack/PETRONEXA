import os
import base64
import asyncio
import concurrent.futures
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

# Module Imports (Engineering Backbone Intact)
from database import init_db, AsyncSessionLocal, UserModel
from auth import get_password_hash, verify_password
from physics import DrillingHydraulicsEngine, WellSegment, DiagnosticEngine
from cementing_engine import PrimaryCementingInput, CementingEngine
from pdf_generator import generate_pdf_payload
from mud_parser import parse_mud_report
from gradients import PressureGradientProfile
from benchmarks import compare_cementing_results

# 1. PAGE CONFIGURATION
PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "⛽"

st.set_page_config(
    page_title="PetroNexa",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================
# SAFE ASYNC RUNNER & DB INIT
# ============================
def run_async_task(coro_fn, *args, **kwargs):
    """Executes an async task inside a clean, isolated background thread."""
    def worker():
        return asyncio.run(coro_fn(*args, **kwargs))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        return future.result()


@st.cache_resource
def bootstrap_database():
    """Initializes database schema once per app lifecycle."""
    run_async_task(init_db)
    return True


bootstrap_database()


# ============================
# RESILIENT ASSET LOADING
# ============================
def get_base64_image(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except (OSError, IOError):
        return ""


logo_base64 = get_base64_image("logo.png")

# ============================
# SESSION STATE INITIALIZATION
# ============================
surface_mw_init = 12.5
default_segments_df = pd.DataFrame([
    {"Segment Name": "Surface Drill Pipe", "Length (ft)": 7000.0, "Pipe OD (in)": 5.0, "Pipe ID (in)": 4.276, "Hole ID (in)": 12.25, "Mud Weight (ppg)": surface_mw_init},
    {"Segment Name": "Heavy Weight Pipe", "Length (ft)": 2000.0, "Pipe OD (in)": 5.0, "Pipe ID (in)": 3.000, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw_init},
    {"Segment Name": "Drill Collars / BHA", "Length (ft)": 1000.0, "Pipe OD (in)": 6.75, "Pipe ID (in)": 2.250, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw_init},
])

defaults = {
    "authenticated": False,
    "user_info": None,
    "auto_pv": None,
    "auto_yp": None,
    "auto_mw": None,
    "parsed": False,
    "latest_results": None,
    "latest_diagnostics": None,
    "sim_metadata": None,
    "cementing_results": None,
    "cementing_params": None,
    "segments_df": default_segments_df,
    "gradient_df": pd.DataFrame({
        "Depth (ft)": [5000.0, 10000.0],
        "Pore Pressure (ppg)": [9.0, 9.5],
        "Fracture Gradient (ppg)": [14.0, 15.5],
    }),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================
# THEME-AWARE STYLING
# ============================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.main-header { font-size: 2.05rem; font-weight: 800; letter-spacing: -0.03em; color: #1e3a8a; margin: 0; line-height: 1.2; }
.sub-header { font-size: 0.92rem; font-weight: 500; color: #475569; margin-top: 0.2rem; margin-bottom: 1.4rem; padding-bottom: 0.7rem; border-bottom: 1px solid #e2e8f0; }
.metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 12px; padding: 1.05rem 1.2rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04); transition: transform 0.15s ease; height: 100%; }
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37,99,235,0.12); }
.metric-card .label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; display: flex; align-items: center; gap: 6px; margin-bottom: 0.3rem; }
.metric-card .value { font-size: 1.55rem; font-weight: 800; color: #1e3a8a; line-height: 1.2; }
.sidebar-heading { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #2563eb; margin-top: 1.2rem; margin-bottom: 0.45rem; }
.section-title { font-size: 1.12rem; font-weight: 700; color: #1e293b; margin-bottom: 0.3rem; display: flex; align-items: center; gap: 0.45rem; }
.section-caption { font-size: 0.84rem; color: #64748b; margin-bottom: 1.15rem; }
.stale-badge { background: #fef3c7; color: #92400e; padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.78rem; font-weight: 600; margin-bottom: 0.8rem; border: 1px solid #fde68a; }
.footer { font-size: 0.72rem; text-align: center; margin-top: 2.8rem; padding-top: 1.1rem; border-top: 1px solid #e2e8f0; color: #94a3b8; }

/* DARK THEME OVERRIDES */
html.theme-dark .main-header, [data-theme="dark"] .main-header { color: #facc15 !important; }
html.theme-dark .sub-header, [data-theme="dark"] .sub-header { color: #94a3b8 !important; border-bottom-color: #1e293b !important; }
html.theme-dark .metric-card, [data-theme="dark"] .metric-card { background: #1e293b !important; border-color: #334155 !important; border-left-color: #facc15 !important; }
html.theme-dark .metric-card .value, [data-theme="dark"] .metric-card .value { color: #facc15 !important; }
html.theme-dark .section-title, [data-theme="dark"] .section-title { color: #e2e8f0 !important; }
html.theme-dark .sidebar-heading, [data-theme="dark"] .sidebar-heading { color: #facc15 !important; }
html.theme-dark .stale-badge, [data-theme="dark"] .stale-badge { background: #451a03 !important; color: #fde68a !important; border-color: #78350f !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ============================
# DEFENSIVE INPUT VALIDATOR
# ============================
def validate_hydraulics_inputs(
    total_depth: float,
    tvd: float,
    flow_rate: float,
    surface_mw: float,
    pv: float,
    yp: float,
    segments_df: pd.DataFrame,
) -> list:
    """Validates physical and geometrical parameters before hydraulics calculations."""
    errors = []

    if total_depth <= 0:
        errors.append("Total Depth (MD) must be greater than zero.")
    if tvd <= 0:
        errors.append("True Vertical Depth (TVD) must be greater than zero.")
    if tvd > total_depth:
        errors.append("TVD cannot exceed Total Depth (MD).")
    if flow_rate <= 0:
        errors.append("Flow rate must be greater than zero.")
    if surface_mw <= 0:
        errors.append("Surface Mud Weight must be greater than zero.")
    if pv < 0:
        errors.append("Plastic Viscosity cannot be negative.")
    if yp < 0:
        errors.append("Yield Point cannot be negative.")

    required_columns = ["Length (ft)", "Pipe OD (in)", "Pipe ID (in)", "Hole ID (in)", "Mud Weight (ppg)"]
    missing = [col for col in required_columns if col not in segments_df.columns]
    if missing:
        errors.extend([f"Missing drill string column: {col}" for col in missing])
        return errors

    if segments_df.empty:
        errors.append("At least one drill-string segment is required.")
        return errors

    for idx, row in segments_df.iterrows():
        seg_num = idx + 1
        try:
            length = float(row["Length (ft)"])
            p_od = float(row["Pipe OD (in)"])
            p_id = float(row["Pipe ID (in)"])
            h_id = float(row["Hole ID (in)"])
            m_wt = float(row["Mud Weight (ppg)"])
        except (TypeError, ValueError):
            errors.append(f"Segment {seg_num}: all geometry and mud-property values must be numeric.")
            continue

        if not np.isfinite([length, p_od, p_id, h_id, m_wt]).all():
            errors.append(f"Segment {seg_num}: values must be finite numbers.")
            continue

        if length <= 0:
            errors.append(f"Segment {seg_num}: Length must be greater than zero.")
        if p_id <= 0:
            errors.append(f"Segment {seg_num}: Pipe ID must be greater than zero.")
        if p_od <= p_id:
            errors.append(f"Segment {seg_num}: Pipe OD ({p_od:.3f} in) must be greater than Pipe ID ({p_id:.3f} in).")
        if h_id <= p_od:
            errors.append(f"Segment {seg_num}: Hole ID ({h_id:.3f} in) must be greater than Pipe OD ({p_od:.3f} in).")
        if m_wt <= 0:
            errors.append(f"Segment {seg_num}: Mud Weight must be greater than zero.")

    return errors


# ============================
# TRANSPARENT SAFETY EVALUATOR
# ============================
def evaluate_drilling_safety(results: dict, target_depth: float, gradient_df: pd.DataFrame):
    """Evaluates ECD relative to pore and fracture pressures dynamically with source tracking."""
    ecd = results.get("ecd_ppg", 0.0)
    gdf = gradient_df.copy().apply(pd.to_numeric, errors="coerce").dropna()
    pore_limit = 9.0
    frac_limit = 15.0
    gradient_source = "Default limits (9.0 / 15.0 ppg)"
    gradient_error = None

    if not gdf.empty:
        try:
            profile = PressureGradientProfile(
                depths=gdf["Depth (ft)"].tolist(),
                pore_pressures=gdf["Pore Pressure (ppg)"].tolist(),
                frac_gradients=gdf["Fracture Gradient (ppg)"].tolist(),
            )
            safe_win = profile.get_safe_window(target_depth)
            frac_limit = safe_win["fracture"]
            pore_limit = safe_win["pore"]
            gradient_source = "Configured pressure-gradient profile"
        except Exception as exc:
            gradient_error = str(exc)

    diag_engine = DiagnosticEngine()
    diag_res = diag_engine.analyze_telemetry(results, baseline_esd_ppg=results.get("surface_mud_weight_ppg"))

    if ecd > frac_limit:
        severity = "RED"
        matched_hazard = "Formation Fracturing Risk"
        msg = f"ECD ({ecd:.2f} ppg) exceeds formation fracture gradient ({frac_limit:.2f} ppg) at target depth."
        rec = "Review pump displacement rate, rheology parameters, and mud-weight program to restore hydraulic operating window."
    elif ecd < pore_limit:
        severity = "YELLOW"
        matched_hazard = "Underbalanced Influx Risk"
        msg = f"ECD ({ecd:.2f} ppg) is below estimated formation pore pressure ({pore_limit:.2f} ppg)."
        rec = "Adjust mud density or circulation parameters to secure required hydrostatic overbalance."
    else:
        severity = "GREEN"
        matched_hazard = "None"
        msg = f"ECD ({ecd:.2f} ppg) is within configured Pore ({pore_limit:.2f} ppg) and Fracture ({frac_limit:.2f} ppg) design boundaries."
        rec = "Hydraulics window is within configured design limits. Continue operations under standard well-control protocol."

    diag_res.update({
        "severity": severity,
        "matched_hazard": matched_hazard,
        "message": msg,
        "recommendation": rec,
        "pore_limit": pore_limit,
        "frac_limit": frac_limit,
        "gradient_source": gradient_source,
        "gradient_error": gradient_error,
    })
    return diag_res


# ============================
# AUTHENTICATION ENGINE
# ============================
async def process_authentication(mode, email_val, password_val, company_val=None):
    email_val = email_val.strip().lower()
    username_val = email_val.split("@")[0].strip()

    async with AsyncSessionLocal() as session:
        if mode == "Register Account":
            try:
                if len(password_val) < 8:
                    return False, "Password must be at least 8 characters long."

                existing = await session.execute(
                    select(UserModel).where(
                        or_(
                            UserModel.email == email_val,
                            UserModel.username == username_val,
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    return False, "Email or username already registered."

                hashed_pw = get_password_hash(password_val)
                new_user = UserModel(
                    username=username_val,
                    email=email_val,
                    hashed_password=hashed_pw,
                    role="drilling_engineer",
                    company_name=(company_val or "").strip(),
                )
                session.add(new_user)
                await session.commit()
                return True, "Account registered! Please switch mode to Login."
            except IntegrityError:
                await session.rollback()
                return False, "Registration failed: email or username already exists."
            except Exception:
                await session.rollback()
                return False, "Registration failed. Please check your details and try again."
        else:
            try:
                result = await session.execute(
                    select(UserModel).where(UserModel.email == email_val)
                )
                user = result.scalar_one_or_none()
                if user and verify_password(password_val, user.hashed_password):
                    return True, {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "company": user.company_name or "",
                    }
                return False, "Invalid email or password."
            except Exception:
                return False, "Login failed. Please check your details and try again."


if not st.session_state.authenticated:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="height: 3.8rem; margin-bottom: 0.9rem;">' if logo_base64 else ''
    st.markdown(
        f"""
        <div style="text-align:center; padding: 2.5rem 0 1.2rem 0;">
            {logo_html}
            <div class="main-header">PetroNexa</div>
            <div class="sub-header" style="border:none; margin-bottom:0;">
                Enterprise Drilling Hydraulics & Diagnostic Engineering Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    auth_mode = st.radio("Select Mode", ["Login", "Register Account"], horizontal=True)
    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        company = None
        if auth_mode == "Register Account":
            company = st.text_input("Company Name", value="Enterprise Hydrocarbons Corp")
        submit = st.form_submit_button("Submit", use_container_width=True)
        if submit:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                success, response = run_async_task(
                    process_authentication, auth_mode, email, password, company
                )
                if auth_mode == "Register Account":
                    if success:
                        st.success(response)
                    else:
                        st.error(response)
                else:
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = response
                        st.rerun()
                    else:
                        st.error(response)
    st.stop()


# ============================
# AUTHENTICATED HEADER
# ============================
h1, h2 = st.columns([1, 11])
with h1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=68)
    else:
        st.markdown("## ⛽")
with h2:
    user_data = st.session_state.user_info or {"username": "Engineer", "company": ""}
    company_display = user_data.get("company") or "Enterprise Hydrocarbons"
    st.markdown(
        f"""
        <div class="main-header" style="margin-top:0.35rem;">PetroNexa</div>
        <div class="sub-header" style="margin-bottom:0.4rem; padding-bottom:0.5rem;">
            <i class="fas fa-user-circle"></i> {user_data.get('username')}
            &nbsp;·&nbsp;
            <i class="fas fa-building"></i> {company_display}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================
# SIDEBAR CONTROL PANEL
# ============================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=34)
    st.markdown("### Project & Well Control")

    with st.expander("Project Details", expanded=False):
        project_name = st.text_input("Project / Well Name", value="Wilcox Deep Target")
        rig_name = st.text_input("Rig Name", value="Rig-05 Executive")

    with st.expander("Well Geometry", expanded=True):
        total_depth = st.number_input("Total Depth / MD (ft)", value=10000.0, step=500.0)
        tvd = st.number_input("True Vertical Depth – TVD (ft)", value=10000.0, step=500.0)
        flow_rate = st.number_input("Flow Rate (GPM)", value=550.0, step=25.0)

    with st.expander("Mud Properties", expanded=True):
        default_mw = st.session_state.auto_mw if st.session_state.auto_mw is not None else 12.5
        surface_mw = st.number_input("Surface Mud Weight (ppg)", value=default_mw, step=0.1)
        default_pv = st.session_state.auto_pv if st.session_state.auto_pv is not None else 22.0
        default_yp = st.session_state.auto_yp if st.session_state.auto_yp is not None else 16.0
        pv = st.number_input("Plastic Viscosity (cP)", value=default_pv, step=1.0)
        yp = st.number_input("Yield Point (lb/100ft²)", value=default_yp, step=1.0)

    st.divider()
    st.markdown('<div class="sidebar-heading"><i class="fas fa-file-upload"></i> Mud Report Upload</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV or Excel", type=["csv", "xlsx"], key="mud_uploader")

    if uploaded_file is not None and not st.session_state.parsed:
        try:
            filename_lower = uploaded_file.name.lower()
            file_type = "csv" if filename_lower.endswith(".csv") else "excel"
            data = parse_mud_report(uploaded_file.read(), file_type)
            st.session_state.auto_pv = data["pv_cp"]
            st.session_state.auto_yp = data["yp"]
            st.session_state.auto_mw = data["mw_ppg"]
            st.session_state.parsed = True
            st.sidebar.success(f"Parsed · PV={data['pv_cp']} · YP={data['yp']} · MW={data['mw_ppg']} ppg")
        except Exception as e:
            st.sidebar.error(f"Parse error: {e}")

    if uploaded_file is None and st.session_state.parsed:
        st.session_state.parsed = False

    st.divider()
    st.markdown('<div class="sidebar-heading"><i class="fas fa-chart-line"></i> Pore / Fracture Gradients</div>', unsafe_allow_html=True)
    grad_df = st.data_editor(
        st.session_state.gradient_df,
        num_rows="dynamic",
        key="gradient_editor",
    )
    st.session_state.gradient_df = grad_df

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()


# ============================
# APPLICATION TABS
# ============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Hydraulics Matrix",
    "3D Well Trajectory",
    "Drilling Diagnostics",
    "Cementing Design",
    "PDF Export",
])

# ---------- TAB 1: HYDRAULICS MATRIX ----------
with tab1:
    st.markdown('<div class="section-title"><i class="fas fa-tachometer-alt"></i> Multi-Segment Drill String Geometry</div>', unsafe_allow_html=True)

    edited_segments = st.data_editor(
        st.session_state["segments_df"],
        num_rows="dynamic",
        use_container_width=True,
        key="segment_editor_grid",
    )
    st.session_state["segments_df"] = edited_segments

    total_seg_length = edited_segments["Length (ft)"].sum() if "Length (ft)" in edited_segments.columns else 0.0
    if abs(total_seg_length - total_depth) > 1.0:
        st.warning(f"⚠️ Drill-string segment total ({total_seg_length:,.0f} ft) does not match configured well MD ({total_depth:,.0f} ft). Verify geometry before proceeding.")

    if st.button("Run Hydraulics Simulation", type="primary", use_container_width=True):
        validation_errors = validate_hydraulics_inputs(
            total_depth,
            tvd,
            flow_rate,
            surface_mw,
            pv,
            yp,
            edited_segments,
        )

        if validation_errors:
            for err in validation_errors:
                st.error(err)
        else:
            with st.spinner("Calculating wellbore hydraulics..."):
                try:
                    engine = DrillingHydraulicsEngine(
                        surface_mud_weight_ppg=surface_mw,
                        flow_rate_gpm=flow_rate,
                        total_depth_ft=total_depth,
                        plastic_viscosity_cp=pv,
                        yield_point_lb_100ft2=yp,
                    )
                    
                    # Instantiate segments matching physics.py dataclass schema
                    for _, row in edited_segments.iterrows():
                        engine.add_segment(
                            WellSegment(
                                name=str(row["Segment Name"]),
                                length_ft=float(row["Length (ft)"]),
                                pipe_od_in=float(row["Pipe OD (in)"]),
                                pipe_id_in=float(row["Pipe ID (in)"]),
                                hole_id_in=float(row["Hole ID (in)"]),
                                mud_weight_ppg=float(row["Mud Weight (ppg)"]),
                                viscosity_cp=pv,
                                yield_point_lb_100ft2=yp,
                            )
                        )

                    results = engine.solve()
                    st.session_state.latest_results = results

                    # Run Safety Diagnostics
                    diag_obj = evaluate_drilling_safety(results, total_depth, st.session_state.gradient_df)
                    st.session_state.latest_diagnostics = diag_obj

                    st.session_state.sim_metadata = {
                        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                        "mw": surface_mw,
                        "flow_rate": flow_rate,
                        "td": total_depth,
                        "tvd": tvd,
                    }

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f'<div class="metric-card"><div class="label">ECD</div><div class="value">{results["ecd_ppg"]:.2f} ppg</div></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="metric-card"><div class="label">Bottom Hole Pressure</div><div class="value">{results["bottom_hole_pressure_psi"]:.1f} psi</div></div>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<div class="metric-card"><div class="label">Annular Pressure Loss</div><div class="value">{results["total_annular_dp_psi"]:.1f} psi</div></div>', unsafe_allow_html=True)
                    with c4:
                        st.markdown(f'<div class="metric-card"><div class="label">Hydrostatic Pressure</div><div class="value">{results["hydrostatic_pressure_psi"]:.1f} psi</div></div>', unsafe_allow_html=True)

                    st.markdown('<div class="section-title" style="margin-top:1.6rem;"><i class="fas fa-list-ul"></i> Segment Breakdown</div>', unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(results["segment_breakdown"]), use_container_width=True)

                except Exception as e:
                    st.error(f"Hydraulics calculation error: {str(e)}")


# ---------- TAB 2: 3D WELL TRAJECTORY ----------
with tab2:
    st.markdown('<div class="section-title"><i class="fas fa-globe"></i> 3D Directional S-Well Profile</div>', unsafe_allow_html=True)

    tc1, tc2, tc3, tc4, tc5 = st.columns(5)
    with tc1:
        kop_ft = st.number_input("Kick-Off Point (KOP ft)", value=2000.0, step=500.0)
    with tc2:
        max_inc_deg = st.number_input("Max Inclination (deg)", value=45.0, min_value=0.0, max_value=180.0, step=5.0)
    with tc3:
        dop_ft = st.number_input("Drop-Off Point (DOP ft)", value=7000.0, step=500.0)
    with tc4:
        final_inc_deg = st.number_input("Final Inclination (deg)", value=0.0, min_value=0.0, max_value=180.0, step=5.0)
    with tc5:
        azimuth_deg = st.number_input("Azimuth Angle (deg)", value=60.0, min_value=0.0, max_value=360.0, step=10.0)

    # TRAJECTORY INTERVAL & BOUNDARY VALIDATION
    traj_errors = []
    if kop_ft <= 0:
        traj_errors.append("Kick-Off Point (KOP) must be greater than zero.")
    if dop_ft <= kop_ft + 500.0:
        traj_errors.append(f"Drop-Off Point ({dop_ft:,.0f} ft) must be at least 500 ft deeper than KOP ({kop_ft:,.0f} ft).")
    if total_depth <= dop_ft + 500.0:
        traj_errors.append(f"Total Depth ({total_depth:,.0f} ft) must be at least 500 ft deeper than DOP ({dop_ft:,.0f} ft).")
    if final_inc_deg > max_inc_deg:
        traj_errors.append("Final inclination cannot exceed maximum inclination.")

    if traj_errors:
        for err in traj_errors:
            st.error(err)
    else:
        build_length = (dop_ft - kop_ft) * 0.4
        build_end = kop_ft + build_length
        drop_end = dop_ft + (total_depth - dop_ft) * 0.6

        md = np.linspace(0, total_depth, 250)
        inc = np.zeros_like(md)
        az = np.radians(np.full_like(md, azimuth_deg))

        for i, depth in enumerate(md):
            if depth <= kop_ft:
                inc[i] = 0.0
            elif kop_ft < depth <= build_end:
                frac = (depth - kop_ft) / (build_end - kop_ft)
                inc[i] = np.radians(max_inc_deg * frac)
            elif build_end < depth <= dop_ft:
                inc[i] = np.radians(max_inc_deg)
            elif dop_ft < depth <= drop_end:
                frac = (depth - dop_ft) / (drop_end - dop_ft)
                current_inc = max_inc_deg - (max_inc_deg - final_inc_deg) * frac
                inc[i] = np.radians(current_inc)
            else:
                inc[i] = np.radians(final_inc_deg)

        x, y, z = np.zeros_like(md), np.zeros_like(md), np.zeros_like(md)
        for i in range(1, len(md)):
            dmd = md[i] - md[i - 1]
            avg_inc = (inc[i] + inc[i - 1]) / 2
            avg_az = (az[i] + az[i - 1]) / 2
            x[i] = x[i - 1] + dmd * np.sin(avg_inc) * np.cos(avg_az)
            y[i] = y[i - 1] + dmd * np.sin(avg_inc) * np.sin(avg_az)
            z[i] = z[i - 1] + dmd * np.cos(avg_inc)

        fig = go.Figure()
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode="lines",
            line=dict(color=z, colorscale="Viridis", width=6, showscale=True, colorbar=dict(title="TVD (ft)")),
            name="S-Well Trajectory",
        ))
        fig.update_layout(
            scene=dict(
                xaxis_title="Easting (ft)", yaxis_title="Northing (ft)", zaxis_title="TVD (ft)",
                zaxis=dict(autorange="reversed"),
            ),
            margin=dict(l=0, r=0, b=0, t=30), height=600,
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------- TAB 3: DRILLING DIAGNOSTICS ----------
with tab3:
    st.markdown('<div class="section-title"><i class="fas fa-microchip"></i> Drilling Diagnostics Engine</div>', unsafe_allow_html=True)

    if st.session_state.latest_diagnostics is not None and st.session_state.sim_metadata is not None:
        meta = st.session_state.sim_metadata
        diag = st.session_state.latest_diagnostics

        st.markdown(
            f'<div class="stale-badge"><i class="fas fa-clock"></i> Active Simulation Timestamp: {meta["timestamp"]} · MW: {meta["mw"]} ppg · Flow: {meta["flow_rate"]} GPM · TD: {meta["td"]:,.0f} ft</div>',
            unsafe_allow_html=True,
        )

        st.caption(f"**Gradient Basis**: {diag.get('gradient_source', 'N/A')}")
        if diag.get("gradient_error"):
            st.warning(f"⚠️ Gradient profile evaluation unfulfilled ({diag['gradient_error']}). Fallback safety limits applied.")

        if diag.get("status") == "CRITICAL" or diag.get("severity") == "RED":
            st.error(f"**CRITICAL EXCURSION**: {diag['message']}")
            st.write(f"• **Recommended Action**: {diag['recommendation']}")
        elif diag.get("status") == "WARNING" or diag.get("status") == "UNDERBALANCED" or diag.get("severity") == "YELLOW":
            st.warning(f"**RISK WARNING**: {diag['message']}")
            st.write(f"• **Recommended Action**: {diag['recommendation']}")
        else:
            st.success(f"**WITHIN CONFIGURED HYDRAULIC WINDOW**: {diag['message']}")
            st.write(f"• **Operational Status**: {diag['recommendation']}")

        if diag.get("flags"):
            for flag in diag["flags"]:
                st.info(f"🚩 {flag}")
    else:
        st.info("Execute hydraulics simulation in the Hydraulics Matrix tab to render diagnostics.")


# ---------- TAB 4: CEMENTING DESIGN ----------
with tab4:
    st.markdown('<div class="section-title"><i class="fas fa-hard-hat"></i> Primary Cementing & Plug Engineering</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        hole_dia = st.number_input("Hole Diameter (in)", value=8.5, min_value=4.0, step=0.5)
        casing_od = st.number_input("Casing OD (in)", value=7.0, min_value=2.0, step=0.5)
        casing_id = st.number_input("Casing ID (in)", value=6.276, min_value=1.0, step=0.1)
        interval_ft = st.number_input("Cemented Interval (ft)", value=5000.0, step=100.0)
        washout_pct = st.number_input("Washout (%)", value=15.0, min_value=0.0, step=1.0)
        shoe_track = st.number_input("Shoe Track (ft)", value=40.0, min_value=0.0, step=5.0)
    with c2:
        lead_dens = st.number_input("Lead Density (ppg)", value=12.5, min_value=1.0, step=0.1)
        tail_dens = st.number_input("Tail Density (ppg)", value=15.8, min_value=1.0, step=0.1)
        spacer_dens = st.number_input("Spacer Density (ppg)", value=11.0, min_value=1.0, step=0.1)
        disp_dens = st.number_input("Displacement Fluid Density (ppg)", value=10.0, min_value=1.0, step=0.1)
        tail_length = st.number_input("Tail Length (ft)", value=500.0, min_value=1.0, step=50.0)
        bht = st.number_input("Bottom Hole Temp (°F)", value=180.0, min_value=32.0, step=5.0)

    spacer_length = st.number_input("Spacer Annular Length (ft)", value=500.0, min_value=0.0, step=50.0)

    if st.button("Run Cementing Calculation", type="primary", use_container_width=True):
        cement_errors = []
        if casing_od <= casing_id:
            cement_errors.append("Casing OD must be strictly greater than Casing ID.")
        if hole_dia <= casing_od:
            cement_errors.append("Hole Diameter must be strictly greater than Casing OD.")
        if interval_ft <= 0:
            cement_errors.append("Cemented interval length must be greater than zero.")
        if shoe_track >= interval_ft:
            cement_errors.append(f"Shoe track length ({shoe_track:,.0f} ft) must be strictly less than cemented interval ({interval_ft:,.0f} ft).")
        if tail_length > interval_ft:
            cement_errors.append(f"Tail slurry length ({tail_length:,.0f} ft) cannot exceed cemented interval ({interval_ft:,.0f} ft).")

        if cement_errors:
            for err in cement_errors:
                st.error(err)
        else:
            try:
                params = PrimaryCementingInput(
                    hole_diameter_in=hole_dia,
                    casing_od_in=casing_od,
                    casing_id_in=casing_id,
                    interval_length_ft=interval_ft,
                    washout_factor_pct=washout_pct,
                    shoe_track_length_ft=shoe_track,
                    lead_slurry_density_ppg=lead_dens,
                    tail_slurry_density_ppg=tail_dens,
                    spacer_density_ppg=spacer_dens,
                    displacement_fluid_density_ppg=disp_dens,
                    tail_slurry_length_ft=tail_length,
                    bht_fahrenheit=bht,
                    spacer_annular_length_ft=spacer_length,
                    true_vertical_depth_ft=tvd,
                )
                engine = CementingEngine()
                result = engine.design_primary_job(params)
                st.session_state.cementing_results = result
                st.session_state.cementing_params = {"casing_od": casing_od, "hole_dia": hole_dia, "interval_ft": interval_ft}

                v1, v2, v3, v4 = st.columns(4)
                v1.metric("Lead Slurry Volume", f"{result['lead_slurry_volume_bbl']:.2f} bbl")
                v2.metric("Tail Slurry Volume", f"{result['tail_slurry_volume_bbl']:.2f} bbl")
                v3.metric("Spacer Volume", f"{result['spacer_volume_bbl']:.2f} bbl")
                v4.metric("Displacement Volume", f"{result['displacement_volume_bbl']:.2f} bbl")

                st.metric("Recommended Plug Bumping Pressure", f"{result['recommended_plug_bumping_pressure_psi']:.1f} psi")

                # BENCHMARK COMPARISON
                st.markdown('<div class="section-title" style="margin-top:1.4rem;"><i class="fas fa-balance-scale"></i> Historical Cementing Benchmarks</div>', unsafe_allow_html=True)
                benchmarks = compare_cementing_results(result)
                st.dataframe(pd.DataFrame(benchmarks), use_container_width=True)

            except Exception as e:
                st.error(f"Cementing design error: {e}")


# ---------- TAB 5: PDF EXPORT ----------
with tab5:
    st.markdown('<div class="section-title"><i class="fas fa-file-pdf"></i> Generate Engineering Report & Compliance Summary</div>', unsafe_allow_html=True)

    if st.session_state.latest_results is not None and st.session_state.latest_diagnostics is not None:
        if st.button("Export Engineering PDF", type="primary", use_container_width=True):
            with st.spinner("Compiling PDF document..."):
                project_meta = {
                    "name": project_name,
                    "rig_name": rig_name,
                    "company": user_data.get("company", ""),
                }

                diag = st.session_state.latest_diagnostics
                diag_meta = {
                    "severity": diag.get("severity", "NORMAL"),
                    "matched_hazard": diag.get("matched_hazard", "None"),
                    "detailed_diagnosis": diag.get("message", "Calculations completed successfully."),
                }

                pdf_buffer = generate_pdf_payload(
                    project_meta,
                    st.session_state.latest_results,
                    diag_meta,
                    engineer_name=user_data.get("username", "Engineer"),
                    cementing_results=st.session_state.get("cementing_results"),
                )
                st.download_button(
                    label="Download Report",
                    data=pdf_buffer,
                    file_name=f"PetroNexa_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
    else:
        st.warning("Calculations must be run in the Hydraulics Matrix prior to report export.")

st.markdown('<div class="footer">© 2026 PetroNexa · Enterprise Drilling Engineering Platform</div>', unsafe_allow_html=True)
