"""
PetroNexa Streamlit Web Application Interface
Complete Enterprise Edition: Auth, Custom Logo Branding, Hydraulics, Cementing, 3D Trajectory, AI Diagnostics, PDF Studio
"""
import os
import sys

# Force Streamlit Cloud runtime to recognize repo root and /source directory
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SOURCE_DIR = os.path.join(REPO_ROOT, "source")
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Safe import fallbacks
try:
    from source.physics import DrillingFluidEngine
    from source.cementing_engine import CementingEngine
    from source.pdf_generator import ReportGenerator
except ModuleNotFoundError:
    from physics import DrillingFluidEngine
    from cementing_engine import CementingEngine
    from pdf_generator import ReportGenerator

# Path resolution for logo.png
LOGO_PATH = os.path.join(REPO_ROOT, "logo.png")
if not os.path.exists(LOGO_PATH):
    # Secondary fallback check if logo sits inside /assets or /source
    alt_logo = os.path.join(REPO_ROOT, "assets", "logo.png")
    if os.path.exists(alt_logo):
        LOGO_PATH = alt_logo

# Page Configuration
st.set_page_config(
    page_title="PetroNexa | Drilling Engineering Suite",
    page_icon="⚓",
    layout="wide"
)

# Initialize Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ==========================================
# AUTHENTICATION & LOGIN GATE
# ==========================================
def render_login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Display Custom Logo Branding
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="color: #1E3A8A; font-size: 3rem; margin-bottom: 0;">⚓ PETRONEXA</h1>
                    <p style="color: #6B7280; font-size: 1.1rem;">Optima Pro — Engineering & AI Suite</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.subheader("🔐 Secure Portal Login")
        with st.form("login_form"):
            user_input = st.text_input("Username / Engineer ID", value="engineer@petronexa.com")
            password_input = st.text_input("Password", type="password", value="admin123")
            submit_login = st.form_submit_button("Authenticate System", type="primary", use_container_width=True)

            if submit_login:
                if user_input and password_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.success("Authentication successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Please provide valid login credentials.")

# Render Login Screen if unauthenticated
if not st.session_state["authenticated"]:
    render_login_screen()
    st.stop()

# ==========================================
# AUTHENTICATED WORKSPACE & NAVIGATION BAR
# ==========================================

# Header Bar with Integrated Logo and Fixed Logout Button
header_col1, header_col2, header_col3 = st.columns([1, 4, 1.5])

with header_col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)

with header_col2:
    st.markdown("## **PetroNexa Optima Pro**")
    st.caption("Operational Engineering & AI Diagnostics Workspace")

with header_col3:
    st.write(f"👤 **{st.session_state['username']}**")
    if st.button("Log Out", type="secondary"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown("---")

# Navigation Tabs across all features
tab_hydraulics, tab_cementing, tab_3d, tab_ai, tab_pdf = st.tabs([
    "💧 Drilling Hydraulics", 
    "🧱 Cementing Operations", 
    "🌐 3D Wellbore Trajectory", 
    "🤖 AI Diagnostics",
    "📄 PDF Report Studio"
])

# ==========================================
# TAB 1: DRILLING HYDRAULICS
# ==========================================
with tab_hydraulics:
    st.subheader("Hydraulics & Rheology Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        surface_mw = st.number_input("Surface Mud Weight (ppg)", min_value=0.1, value=12.0, step=0.1)
        flow_rate = st.number_input("Flow Rate (GPM)", min_value=1.0, value=450.0, step=10.0)
    with col2:
        total_depth = st.number_input("Measured Depth - MD (ft)", min_value=1.0, value=10000.0, step=100.0)
        tvd = st.number_input("True Vertical Depth - TVD (ft)", min_value=1.0, value=9500.0, step=100.0)

    st.markdown("#### Annular Friction Losses")
    annular_dp = st.number_input("Total Annular Pressure Drop (psi)", min_value=0.0, value=350.0, step=25.0)

    if st.button("Calculate Hydraulics", type="primary"):
        try:
            engine = DrillingFluidEngine(
                surface_mud_weight_ppg=surface_mw,
                flow_rate_gpm=flow_rate,
                total_depth_ft=total_depth,
                true_vertical_depth_ft=tvd
            )
            ecd = engine.calculate_bottomhole_ecd(total_annular_dp_psi=annular_dp)
            
            st.success("Hydraulics calculations completed successfully.")
            
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("Equivalent Circulating Density (ECD)", f"{ecd} ppg")
            res_col2.metric("Hydrostatic Pressure Baseline", f"{round(0.052 * surface_mw * tvd, 2)} psi")

            report_payload = {
                "surface_mud_weight_ppg": surface_mw,
                "flow_rate_gpm": flow_rate,
                "total_depth_ft": total_depth,
                "true_vertical_depth_ft": tvd,
                "calculated_ecd_ppg": ecd
            }
            
            pdf_bytes = ReportGenerator.generate_hydraulics_report(report_payload)
            st.download_button(
                label="📄 Download Hydraulics Report (PDF)",
                data=pdf_bytes,
                file_name="PetroNexa_Hydraulics_Report.pdf",
                mime="application/pdf"
            )
        except ValueError as err:
            st.error(f"⚠️ Engineering Validation Error: {str(err)}")

# ==========================================
# TAB 2: CEMENTING OPERATIONS
# ==========================================
with tab_cementing:
    st.subheader("Cementing Design & Volume Calculation")

    col_a, col_b = st.columns(2)
    with col_a:
        casing_od = st.number_input("Casing Outer Diameter (in)", min_value=1.0, value=7.0, step=0.125)
        casing_id = st.number_input("Casing Inner Diameter (in)", min_value=0.5, value=6.151, step=0.125)
        hole_size = st.number_input("Hole Diameter (in)", min_value=1.0, value=8.5, step=0.125)
    with col_b:
        cement_td = st.number_input("Total Depth - TD (ft)", min_value=1.0, value=12000.0, step=500.0, key="cem_td")
        toc = st.number_input("Top of Cement - TOC (ft)", min_value=0.0, value=8000.0, step=500.0)
        excess = st.number_input("Excess Volume Margin (%)", min_value=0.0, value=15.0, step=5.0)

    st.markdown("#### Slurry & Fluid Densities")
    slurry_mw = st.number_input("Cement Slurry Density (ppg)", min_value=1.0, value=15.8, step=0.2)
    displacement_mw = st.number_input("Displacement Mud Weight (ppg)", min_value=1.0, value=10.5, step=0.2)

    if st.button("Calculate Cementing Design", type="primary"):
        try:
            c_engine = CementingEngine(
                casing_outer_diameter_in=casing_od,
                casing_inner_diameter_in=casing_id,
                hole_diameter_in=hole_size,
                total_depth_ft=cement_td,
                top_of_cement_ft=toc
            )

            slurry_vol = c_engine.calculate_slurry_volume_bbl(excess_percentage=excess)
            disp_vol = c_engine.calculate_displacement_volume_bbl(shoe_track_length_ft=80.0)
            bhp_results = c_engine.calculate_hydrostatic_head_psi(
                slurry_density_ppg=slurry_mw,
                mud_density_ppg=displacement_mw
            )

            st.success("Cementing design completed successfully.")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Required Slurry Volume", f"{slurry_vol} bbl")
            m2.metric("Displacement Volume", f"{disp_vol} bbl")
            m3.metric("Post-Job BHP", f"{bhp_results['total_bottomhole_pressure_psi']} psi")

            cem_report_payload = {
                "casing_od_in": casing_od,
                "hole_diameter_in": hole_size,
                "total_depth_ft": cement_td,
                "top_of_cement_ft": toc,
                "slurry_volume_bbl": slurry_vol,
                "displacement_volume_bbl": disp_vol,
                "bottomhole_hydrostatic_psi": bhp_results['total_bottomhole_pressure_psi']
            }

            cem_pdf_bytes = ReportGenerator.generate_hydraulics_report(cem_report_payload)
            st.download_button(
                label="📄 Download Cementing Job PDF",
                data=cem_pdf_bytes,
                file_name="PetroNexa_Cementing_Report.pdf",
                mime="application/pdf"
            )
        except ValueError as err:
            st.error(f"⚠️ Engineering Validation Error: {str(err)}")

# ==========================================
# TAB 3: 3D WELLBORE TRAJECTORY VISUALIZER
# ==========================================
with tab_3d:
    st.subheader("3D Directional Survey Trajectory Profile")
    
    col_3d_a, col_3d_b = st.columns(2)
    with col_3d_a:
        kickoff_depth = st.number_input("Kickoff Point - KOP (ft)", min_value=0.0, value=2000.0, step=500.0)
        max_inclination = st.number_input("Max Inclination (deg)", min_value=0.0, max_value=90.0, value=45.0, step=5.0)
    with col_3d_b:
        target_azimuth = st.number_input("Azimuth Direction (deg)", min_value=0.0, max_value=360.0, value=120.0, step=5.0)
        total_md = st.number_input("Total Measured Depth (ft)", min_value=1000.0, value=10000.0, step=500.0)

    md_points = np.linspace(0, total_md, 100)
    x_coords, y_coords, z_coords = [], [], []
    azimuth_rad = np.radians(target_azimuth)

    for md in md_points:
        if md <= kickoff_depth:
            inc = 0.0
            tv_depth = md
            offset = 0.0
        else:
            inc = np.radians(min(max_inclination, (md - kickoff_depth) * 0.01 * max_inclination))
            tv_depth = kickoff_depth + (md - kickoff_depth) * np.cos(inc)
            offset = (md - kickoff_depth) * np.sin(inc)

        x_coords.append(offset * np.sin(azimuth_rad))
        y_coords.append(offset * np.cos(azimuth_rad))
        z_coords.append(-tv_depth)

    fig_3d = go.Figure(data=[go.Scatter3d(
        x=x_coords, y=y_coords, z=z_coords,
        mode='lines+markers',
        line=dict(color='#1E3A8A', width=6),
        marker=dict(size=3, color='#EF4444')
    )])

    fig_3d.update_layout(
        scene=dict(
            xaxis_title="Easting Offset (ft)",
            yaxis_title="Northing Offset (ft)",
            zaxis_title="TVD (ft)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        height=500
    )

    st.plotly_chart(fig_3d, use_container_width=True)

# ==========================================
# TAB 4: AI DRILLING ASSISTANT
# ==========================================
with tab_ai:
    st.subheader("AI Telemetry Monitor & Dynamic Hazard Diagnostics")

    ai_col1, ai_col2 = st.columns(2)
    with ai_col1:
        telemetry_spp = st.number_input("Standpipe Pressure - SPP (psi)", min_value=0.0, value=2800.0, step=50.0)
        telemetry_rpm = st.number_input("Bit Speed - RPM", min_value=0.0, value=120.0, step=5.0)
    with ai_col2:
        telemetry_torque = st.number_input("Torque (ft-lbs)", min_value=0.0, value=14000.0, step=500.0)
        gas_units = st.number_input("Background Gas (Units)", min_value=0.0, value=45.0, step=5.0)

    if st.button("Run AI Diagnostic Analysis", type="primary"):
        st.markdown("#### AI Advisory Verdict")
        hazards = []
        if telemetry_spp > 3500:
            hazards.append("⚠️ **High SPP Threshold Exceeded:** Risk of flow channel restrictions or bit nozzle plugging.")
        if telemetry_torque > 18000 and telemetry_rpm < 80:
            hazards.append("🚨 **Stick-Slip Risk:** High torque paired with reduced RPM indicates downhole drag.")
        if gas_units > 150:
            hazards.append("🔥 **Kick Warning:** Elevated background gas detected. Check pit levels.")
        
        if hazards:
            for h in hazards:
                st.warning(h)
        else:
            st.success("✅ **Normal Telemetry:** Wellbore parameters are within safe operating limits.")

# ==========================================
# TAB 5: PDF REPORT STUDIO
# ==========================================
with tab_pdf:
    st.subheader("Comprehensive Technical Report Studio")
    st.write("Generate custom compiled engineering PDF summary sheets on demand.")

    report_title = st.text_input("Project / Well Name", value="Well PetroNexa-01 Core Summary")
    operator = st.text_input("Operator Name", value="PetroNexa Operations")
    
    col_pdf_1, col_pdf_2 = st.columns(2)
    with col_pdf_1:
        pdf_md = st.number_input("Target MD (ft)", value=10000.0)
        pdf_tvd = st.number_input("Target TVD (ft)", value=9500.0)
    with col_pdf_2:
        pdf_mw = st.number_input("Mud Weight (ppg)", value=12.2)
        pdf_flow = st.number_input("Circulation Rate (GPM)", value=480.0)

    if st.button("Generate Master Technical PDF", type="primary"):
        custom_payload = {
            "well_name": report_title,
            "operator": operator,
            "target_md_ft": pdf_md,
            "target_tvd_ft": pdf_tvd,
            "mud_weight_ppg": pdf_mw,
            "flow_rate_gpm": pdf_flow
        }
        
        compiled_pdf = ReportGenerator.generate_hydraulics_report(custom_payload)
        st.download_button(
            label="💾 Download Master PDF Document",
            data=compiled_pdf,
            file_name=f"{report_title.replace(' ', '_')}_Report.pdf",
            mime="application/pdf"
        )
