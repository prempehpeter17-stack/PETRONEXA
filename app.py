"""
PetroNexa Streamlit Web Application Interface
"""
import os
import sys

# Force Streamlit Cloud runtime to recognize both repo root and /source directory
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SOURCE_DIR = os.path.join(REPO_ROOT, "source")
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

import streamlit as st

# Safe import try/except block to handle root and module package imports
try:
    from source.physics import DrillingFluidEngine
    from source.cementing_engine import CementingEngine
    from source.pdf_generator import ReportGenerator
except ModuleNotFoundError:
    from physics import DrillingFluidEngine
    from cementing_engine import CementingEngine
    from pdf_generator import ReportGenerator

# Page Configuration & Styling
st.set_page_config(
    page_title="PetroNexa | Petroleum Engineering Suite",
    page_icon="⚓",
    layout="wide"
)

st.title("⚓ PetroNexa Engineering Operations")
st.markdown("---")

# Application Navigation Tabs
tab_hydraulics, tab_cementing = st.tabs(["💧 Drilling Hydraulics", "🧱 Cementing Operations"])

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
