"""PetroNexa Streamlit Reservoir Engineering UI."""
import pandas as pd
import streamlit as st

from reservoir import ReservoirEngineeringEngine


def _show_result(result: dict):
    rows = []
    for key, value in result.items():
        label = key.replace("_", " ").title()
        if isinstance(value, (int, float)):
            rows.append({"Parameter": label, "Value": f"{value:,.4g}"})
        else:
            rows.append({"Parameter": label, "Value": value})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_reservoir_workspace():
    """Render reservoir calculations independently from drilling hydraulics."""
    st.markdown('<div class="section-title">🛢️ Reservoir Engineering</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Reservoir properties, Darcy flow, radial flow, material balance, IPR and productivity calculations.</div>',
        unsafe_allow_html=True,
    )

    tool = st.selectbox(
        "Reservoir Calculation",
        [
            "Reservoir Properties",
            "Darcy Flow Rate",
            "Radial Flow",
            "Productivity Index",
            "Vogel IPR",
            "Material Balance",
        ],
        key="reservoir_tool",
    )

    if tool == "Reservoir Properties":
        c1, c2 = st.columns(2)
        with c1:
            bulk = st.number_input("Bulk Rock Volume (acre-ft)", value=100.0, min_value=0.001)
            ntg = st.number_input("Net-to-Gross", value=0.80, min_value=0.001, max_value=1.0, step=0.01)
            porosity = st.number_input("Porosity", value=0.20, min_value=0.001, max_value=1.0, step=0.01)
        with c2:
            sw = st.number_input("Water Saturation", value=0.30, min_value=0.001, max_value=1.0, step=0.01)
            perm = st.number_input("Permeability (md)", value=100.0, min_value=0.001)
            cr = st.number_input("Rock Compressibility (1/psi)", value=0.0, min_value=0.0, format="%.6g")
        cw = st.number_input("Water Compressibility (1/psi)", value=0.0, min_value=0.0, format="%.6g")
        if st.button("Calculate Reservoir Properties", type="primary", use_container_width=True):
            try:
                _show_result(ReservoirEngineeringEngine.properties(bulk, ntg, porosity, sw, perm, cr, cw))
            except Exception as exc:
                st.error(f"Reservoir calculation error: {exc}")

    elif tool == "Darcy Flow Rate":
        c1, c2 = st.columns(2)
        with c1:
            k = st.number_input("Permeability (md)", value=100.0, min_value=0.001)
            h = st.number_input("Net Thickness (ft)", value=50.0, min_value=0.001)
            dp = st.number_input("Pressure Drop (psi)", value=500.0, min_value=0.001)
        with c2:
            mu = st.number_input("Oil Viscosity (cP)", value=2.0, min_value=0.001)
            bo = st.number_input("Oil FVF, Bo (rb/STB)", value=1.20, min_value=0.001)
            length = st.number_input("Flow Length (ft)", value=1000.0, min_value=0.001)
        if st.button("Calculate Darcy Rate", type="primary", use_container_width=True):
            try:
                result = ReservoirEngineeringEngine.darcy_rate(k, h, dp, mu, bo, length)
                st.metric("Oil Rate", f"{result['oil_rate_stb_day']:,.2f} STB/day")
                _show_result(result)
            except Exception as exc:
                st.error(f"Darcy calculation error: {exc}")

    elif tool == "Radial Flow":
        c1, c2 = st.columns(2)
        with c1:
            k = st.number_input("Permeability (md)", value=100.0, min_value=0.001)
            h = st.number_input("Net Thickness (ft)", value=50.0, min_value=0.001)
            pr = st.number_input("Reservoir Pressure (psi)", value=3500.0, min_value=0.001)
            pwf = st.number_input("Bottomhole Pressure (psi)", value=2500.0, min_value=0.0)
        with c2:
            mu = st.number_input("Oil Viscosity (cP)", value=2.0, min_value=0.001)
            bo = st.number_input("Oil FVF, Bo (rb/STB)", value=1.20, min_value=0.001)
            re = st.number_input("Drainage Radius (ft)", value=2000.0, min_value=0.001)
            rw = st.number_input("Wellbore Radius (ft)", value=0.35, min_value=0.001)
        skin = st.number_input("Skin", value=0.0, step=0.5)
        if st.button("Calculate Radial Flow", type="primary", use_container_width=True):
            try:
                result = ReservoirEngineeringEngine.radial_flow(k, h, pr, pwf, mu, bo, re, rw, skin)
                a, b = st.columns(2)
                a.metric("Oil Rate", f"{result['oil_rate_stb_day']:,.2f} STB/day")
                b.metric("Productivity Index", f"{result['productivity_index_stb_day_psi']:,.4f} STB/day/psi")
                _show_result(result)
            except Exception as exc:
                st.error(f"Radial-flow calculation error: {exc}")

    elif tool == "Productivity Index":
        c1, c2, c3 = st.columns(3)
        with c1:
            q = st.number_input("Test Rate (STB/day)", value=500.0, min_value=0.001)
        with c2:
            pr = st.number_input("Reservoir Pressure (psi)", value=3000.0, min_value=0.001)
        with c3:
            pwf = st.number_input("Bottomhole Pressure (psi)", value=2500.0, min_value=0.0)
        if st.button("Calculate Productivity Index", type="primary", use_container_width=True):
            try:
                result = ReservoirEngineeringEngine.productivity_index(q, pr, pwf)
                st.metric("Productivity Index", f"{result['productivity_index_stb_day_psi']:,.4f} STB/day/psi")
                _show_result(result)
            except Exception as exc:
                st.error(f"PI calculation error: {exc}")

    elif tool == "Vogel IPR":
        c1, c2 = st.columns(2)
        with c1:
            pr = st.number_input("Reservoir Pressure (psi)", value=3000.0, min_value=0.001)
            qt = st.number_input("Test Oil Rate (STB/day)", value=500.0, min_value=0.001)
        with c2:
            pwft = st.number_input("Test BHP (psi)", value=1800.0, min_value=0.0)
            pwftarget = st.number_input("Target BHP (psi)", value=1500.0, min_value=0.0)
        if st.button("Calculate Vogel IPR", type="primary", use_container_width=True):
            try:
                result = ReservoirEngineeringEngine.vogel_ipr(pr, qt, pwft, pwftarget)
                a, b = st.columns(2)
                a.metric("Maximum Oil Rate", f"{result['maximum_oil_rate_stb_day']:,.2f} STB/day")
                b.metric("Target Oil Rate", f"{result['target_oil_rate_stb_day']:,.2f} STB/day")
                _show_result(result)
            except Exception as exc:
                st.error(f"Vogel IPR calculation error: {exc}")

    else:
        c1, c2 = st.columns(2)
        with c1:
            F = st.number_input("Underground Withdrawal, F (rb)", value=500000.0, min_value=0.001)
            We = st.number_input("Water Influx, We (rb)", value=100000.0, min_value=0.0)
            Eo = st.number_input("Oil Expansion, Eo", value=2.0, min_value=0.001)
        with c2:
            m = st.number_input("Gas-Cap Ratio, m", value=0.5, min_value=0.0)
            Eg = st.number_input("Gas-Cap Expansion, Eg", value=1.5, min_value=0.0)
            Efw = st.number_input("Formation-Water Expansion, Efw", value=0.2, min_value=0.0)
        if st.button("Calculate Material Balance", type="primary", use_container_width=True):
            try:
                result = ReservoirEngineeringEngine.material_balance(F, We, Eo, m, Eg, Efw)
                st.metric("Estimated OOIP", f"{result['original_oil_in_place_stb']:,.2f} STB")
                _show_result(result)
            except Exception as exc:
                st.error(f"Material-balance calculation error: {exc}")