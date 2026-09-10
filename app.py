"""
PetroNexa Streamlit Web Application Interface
Operational UI Edition: Intuitive Gauges, Visual Status Cards, and Modern Engineering Layouts
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
    alt_logo = os.path.join(REPO_ROOT, "assets", "logo.png")
    if os.path.exists(alt_logo):
        LOGO_PATH = alt_logo

# Page Configuration
st.set_page_config(
    page_title="PetroNexa | Operations Control Center",
    page_icon="⚓",
    layout="wide"
)

# Custom Styling for Practical Operations Theme
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-ok {
        background-color: #ecfdf5;
        border-left: 5px solid #10b981;
        padding: 12px;
        border-radius: 6px;
        color: #065f46;
    }
    .status-warn {
        background-color: #fffbebf;
        border-left: 5px solid #f59e0b;
        padding: 12px;
        border-radius: 6px;
        color: #92400e;
    }
    .status-alert {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 12px;
        border-radius: 6px;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ==========================================
# AUTHENTICATION PORTAL
# ==========================================
def render_login_screen():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown(
                """
                <div style="text-align: center;">
                    <h1 style="color: #1E3A8A; font-weight: 800; margin-bottom: 0;">⚓ PETRONEXA</h1>
                    <p style="color: #64748B;">Operations & AI Decision Control Center</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with st.container():
            st.markdown("#### 🔐 Secure Operations Sign-In")
            user_input = st.text_input("Engineer ID / Username", value="engineer@petronexa.com")
            password_input = st.text_input("Access Pin / Password", type="password", value="admin123")
            
            if st.button("Access Dashboard", type="primary", use_container_width=True):
                if user_input and password_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.rerun()
                else:
                    st.error("Please enter authorized credentials.")

if not st.session_state["authenticated"]:
    render_login_screen()
    st.stop()

# ==========================================
# HEADER BAR & USER ACCOUNT
# ==========================================
header_col1, header_col2, header_col3 = st.columns([0.8, 4, 1.2])

with header_col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=90)

with header_col2:
    st.markdown("<h2 style='margin:0; padding:0;'>PetroNexa | Operations Control Center</h2>", unsafe_allow_html=True)
    st.caption("Real-Time Hydraulics, Directional Surveying & AI Hazard Intelligence Engine")

with header_col3:
    st.markdown(f"👤 **{st.session_state['username']}**")
    if st.button("Log Out", type="secondary"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown("---")

# MAIN WORKSPACE TABS
tab_hydraulics, tab_cementing, tab_3d, tab_ai, tab_pdf = st.tabs([
    "💧 Hydraulics Control", 
    "🧱 Cementing Studio", 
    "🌐 3D Well Path", 
    "🤖 AI Hazard Monitor",
    "📄 Report Center"
])

# ==========================================
# TAB 1: DRILLING HYDRAULICS (VISUAL CONTROLS)
# ==========================================
with tab_hydraulics:
    st.subheader("Hydraulics & Pressure Envelope")
    
    col_input, col_viz = st.columns([1.2, 2])
    
    with col_input:
        st.markdown("##### 🎛️ Well Operations Parameters")
        surface_mw = st.slider("Surface Mud Density (ppg)", 8.0, 18.0, 12.0, 0.1)
        flow_rate = st.slider("Circulation Rate (GPM)", 100, 1200, 450, 25)
        total_depth = st.number_input("Measured Depth - MD (ft)", value=10000.0, step=250.0)
        tvd = st.number_input("True Vertical Depth - TVD (ft)", value=9500.0, step=250.0)
        annular_dp = st.slider("Annular Friction Loss (psi)", 50, 1500, 350, 25)

        run_hyd = st.button("Run Hydraulics Calculation", type="primary", use_container_width=True)

    with col_viz:
        if run_hyd or True:  # Instant initial rendering
            try:
                engine = DrillingFluidEngine(
                    surface_mud_weight_ppg=surface_mw,
                    flow_rate_gpm=flow_rate,
                    total_depth_ft=total_depth,
                    true_vertical_depth_ft=tvd
                )
                ecd = engine.calculate_bottomhole_ecd(total_annular_dp_psi=annular_dp)
                hydrostatic = round(0.052 * surface_mw * tvd, 2)

                # Visual Gauges & KPI Summary Cards
                kpi1, kpi2 = st.columns(2)
                with kpi1:
                    st.metric("Equivalent Circulating Density", f"{ecd} ppg", delta=f"{round(ecd - surface_mw, 2)} ppg delta")
                with kpi2:
                    st.metric("Bottomhole Hydrostatic", f"{hydrostatic} psi")

                # Plotly Visual Gauge for Operational Safety Margin
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=ecd,
                    title={'text': "ECD Operating Gauge (ppg)"},
                    gauge={
                        'axis': {'range': [8.0, 20.0]},
                        'bar': {'color': "#1E3A8A"},
                        'steps': [
                            {'range': [8.0, 10.0], 'color': "#dcfce7"},
                            {'range': [10.0, 15.0], 'color': "#e0f2fe"},
                            {'range': [15.0, 18.0], 'color': "#fef3c7"},
                            {'range': [18.0, 20.0], 'color': "#fee2e2"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 17.5
                        }
                    }
                ))
                fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            except Exception as err:
                st.error(f"Calculation Error: {str(err)}")

# ==========================================
# TAB 2: CEMENTING OPERATIONS
# ==========================================
with tab_cementing:
    st.subheader("Casing & Cementing Operations")

    c_col1, c_col2 = st.columns([1, 1])
    
    with c_col1:
        st.markdown("##### 📐 Geometry & Depth Specs")
        casing_od = st.selectbox("Casing Outer Diameter (in)", [9.625, 7.0, 5.5], index=1)
        casing_id = st.number_input("Casing Inner Diameter (in)", value=6.151)
        hole_size = st.selectbox("Hole Diameter (in)", [12.25, 8.5, 6.125], index=1)
        cement_td = st.number_input("Total Depth - TD (ft)", value=12000.0)
        toc = st.number_input("Top of Cement - TOC (ft)", value=8000.0)
    
    with c_col2:
        st.markdown("##### 🧪 Slurry & Displacement Density")
        slurry_mw = st.slider("Cement Slurry Density (ppg)", 12.0, 18.0, 15.8, 0.1)
        displacement_mw = st.slider("Displacement Mud Weight (ppg)", 8.0, 15.0, 10.5, 0.1)
        excess = st.slider("Open Hole Excess (%)", 0, 50, 15, 5)

    if st.button("Compute Cementing Volumes", type="primary"):
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

            st.markdown("---")
            st.markdown("##### 📊 Computed Job Summary")
            r1, r2, r3 = st.columns(3)
            r1.metric("Cement Slurry Volume", f"{slurry_vol} bbl")
            r2.metric("Displacement Volume", f"{disp_vol} bbl")
            r3.metric("Hydrostatic Pressure at Shoe", f"{bhp_results['total_bottomhole_pressure_psi']} psi")

        except Exception as err:
            st.error(f"Execution Error: {str(err)}")

# ==========================================
# TAB 3: 3D WELLBORE TRAJECTORY
# ==========================================
with tab_3d:
    st.subheader("Interactive 3D Directional Survey")

    p_col1, p_col2 = st.columns([1, 2.5])

    with p_col1:
        st.markdown("##### 🧭 Survey Inputs")
        kickoff_depth = st.slider("Kickoff Point - KOP (ft)", 500, 5000, 2000, 100)
        max_inclination = st.slider("Max Inclination (°)", 0, 90, 45, 1)
        target_azimuth = st.slider("Target Azimuth (°)", 0, 360, 120, 5)
        total_md = st.number_input("Total MD (ft)", value=10000.0)

    with p_col2:
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
            line=dict(color='#0284c7', width=6),
            marker=dict(size=3, color='#f43f5e')
        )])

        fig_3d.update_layout(
            scene=dict(
                xaxis_title="Easting (ft)",
                yaxis_title="Northing (ft)",
                zaxis_title="TVD (ft)",
                camera=dict(eye=dict(x=1.4, y=1.4, z=1.0))
            ),
            margin=dict(l=0, r=0, b=0, t=10),
            height=480
        )
        st.plotly_chart(fig_3d, use_container_width=True)

# ==========================================
# TAB 4: AI HAZARD MONITOR
# ==========================================
with tab_ai:
    st.subheader("AI Rig Telemetry & Hazard Diagnostic Center")

    tele_col, alert_col = st.columns([1.2, 1.8])

    with tele_col:
        st.markdown("##### 📡 Live Rig Telemetry Simulation")
        spp = st.number_input("Standpipe Pressure - SPP (psi)", value=2800.0, step=100.0)
        rpm = st.slider("Bit Rotary Speed (RPM)", 0, 250, 120)
        torque = st.number_input("Top Drive Torque (ft-lbs)", value=14000.0, step=500.0)
        gas = st.number_input("Background Gas (Units)", value=45.0, step=5.0)

    with alert_col:
        st.markdown("##### 🛡️ AI Operational Health Verdict")
        
        hazards = []
        if spp > 3500:
            hazards.append(("HIGH SPP DETECTED", "Pressure exceeds 3500 psi limit. Inspect bit nozzles or flow path for restriction."))
        if torque > 18000 and rpm < 80:
            hazards.append(("STICK-SLIP RISK", "High torque combined with low RPM indicates severe downhole drag or mechanical binding."))
        if gas > 150:
            hazards.append(("WELL INFLUX / KICK WARNING", "Gas levels exceeding safe threshold. Perform flow check immediately."))

        if hazards:
            for title, desc in hazards:
                st.markdown(f"""
                <div class="status-alert">
                    <strong>🚨 {title}</strong><br>
                    <small>{desc}</small>
                </div><br>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-ok">
                <strong>✅ Safe Operational Window</strong><br>
                <small>All telemetry parameters are within nominal safety thresholds.</small>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 5: PDF REPORT STUDIO
# ==========================================
with tab_pdf:
    st.subheader("Automated Engineering PDF Exporter")

    pdf_col1, pdf_col2 = st.columns(2)
    with pdf_col1:
        well_id = st.text_input("Well Name / ID", value="Well PetroNexa-01 Summary")
        operator_id = st.text_input("Operator / Service Company", value="PetroNexa Operations")
    
    with pdf_col2:
        pdf_md_val = st.number_input("Total MD (ft)", value=10000.0)
        pdf_mw_val = st.number_input("Mud Density (ppg)", value=12.2)

    if st.button("Generate & Download PDF Executive Report", type="primary"):
        payload = {
            "well_name": well_id,
            "operator": operator_id,
            "target_md_ft": pdf_md_val,
            "mud_weight_ppg": pdf_mw_val,
            "flow_rate_gpm": 450.0
        }
        pdf_data = ReportGenerator.generate_hydraulics_report(payload)
        st.download_button(
            label="💾 Save PDF Document",
            data=pdf_data,
            file_name=f"{well_id.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
