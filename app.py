import os
import html
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

# Module Imports
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



# Modular discipline UIs
from ui.drilling import render_drilling_sidebar, render_drilling_workspace
from ui.reservoir import render_reservoir_workspace

# ============================
# AUTHENTICATION ENGINE
# ============================
async def process_authentication(mode, email_val, password_val, profile=None):
    """Register or authenticate a user using the web-app account profile."""
    email_val = email_val.strip().lower()
    profile = profile or {}

    async with AsyncSessionLocal() as session:
        if mode == "Register Account":
            try:
                username_val = (profile.get("username") or "").strip()
                full_name_val = (profile.get("full_name") or "").strip()
                if len(password_val) < 8:
                    return False, "Password must be at least 8 characters long."
                if not full_name_val:
                    return False, "Please enter your full name."
                if len(username_val) < 2:
                    return False, "Username must contain at least 2 characters."
                if "@" not in email_val or email_val.startswith("@") or email_val.endswith("@"):
                    return False, "Please enter a valid email address."
                if profile.get("account_type") not in {"student", "professional"}:
                    return False, "Please choose Student or Professional."
                if profile.get("account_type") == "student" and not (profile.get("study_level") and profile.get("programme")):
                    return False, "Please provide your study level and programme."
                if profile.get("account_type") == "professional" and not profile.get("job_title"):
                    return False, "Please select your job title or specialisation."

                existing = await session.execute(
                    select(UserModel).where(
                        or_(UserModel.email == email_val, UserModel.username == username_val)
                    )
                )
                if existing.scalar_one_or_none():
                    return False, "Email or username already registered. Please sign in or choose another."

                new_user = UserModel(
                    username=username_val,
                    email=email_val,
                    hashed_password=get_password_hash(password_val),
                    # Account type personalises the workspace; it is not an authorisation role.
                    role="drilling_engineer",
                    company_name=(profile.get("organisation") or "").strip(),
                    full_name=full_name_val,
                    phone_number=(profile.get("phone_number") or "").strip(),
                    country=(profile.get("country") or "").strip(),
                    account_type=profile.get("account_type", "professional"),
                    study_level=(profile.get("study_level") or "").strip(),
                    programme=(profile.get("programme") or "").strip(),
                    job_title=(profile.get("job_title") or "").strip(),
                    sms_opt_in=bool(profile.get("sms_opt_in", False)),
                )
                session.add(new_user)
                await session.commit()
                return True, "Account created successfully. You can now sign in. SMS delivery will require a configured messaging provider."
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
                        "full_name": getattr(user, "full_name", "") or user.username,
                        "email": user.email,
                        "phone_number": getattr(user, "phone_number", "") or "",
                        "role": user.role,
                        "account_type": getattr(user, "account_type", "professional") or "professional",
                        "company": user.company_name or "",
                        "country": getattr(user, "country", "") or "",
                        "study_level": getattr(user, "study_level", "") or "",
                        "programme": getattr(user, "programme", "") or "",
                        "job_title": getattr(user, "job_title", "") or "",
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
                Petroleum Engineering Workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    auth_mode = st.radio("Welcome to PetroNexa", ["Login", "Register Account"], horizontal=True)
    account_type = "professional"
    if auth_mode == "Register Account":
        account_type = st.radio(
            "I am registering as",
            ["Tertiary Student", "Working Professional"],
            horizontal=True,
            key="registration_account_type",
        )
        account_type = "student" if account_type == "Tertiary Student" else "professional"

    with st.form("auth_form"):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password (minimum 8 characters)", type="password")
        profile = {}
        if auth_mode == "Register Account":
            st.caption("Create your account. Fields marked by the form are used to personalise your workspace.")
            profile["full_name"] = st.text_input("Full name", placeholder="Your first and last name")
            profile["username"] = st.text_input("Username", placeholder="Choose a unique username")
            profile["phone_number"] = st.text_input("Mobile number", placeholder="Include country code, e.g. +233...")
            profile["country"] = st.text_input("Country", value="Ghana")
            profile["account_type"] = account_type
            profile["organisation"] = st.text_input(
                "University or institution" if account_type == "student" else "Company name (or Independent)",
                placeholder="Enter your institution or company",
            )
            if account_type == "student":
                profile["study_level"] = st.selectbox(
                    "Level of study",
                    ["Undergraduate", "Postgraduate — Master's", "Doctoral — PhD", "Diploma or other"],
                )
                profile["programme"] = st.text_input("Programme of study", value="Petroleum Engineering")
                profile["job_title"] = ""
            else:
                profile["job_title"] = st.selectbox(
                    "Job title or specialisation",
                    ["Petroleum Engineer", "Drilling Engineer", "Reservoir Engineer", "Production Engineer", "Petrophysicist", "Other engineering role"],
                )
                profile["study_level"] = ""
                profile["programme"] = ""
            profile["sms_opt_in"] = st.checkbox(
                "I agree to receive optional PetroNexa SMS updates and product announcements."
            )
            st.caption("SMS delivery is not active until PetroNexa connects to an SMS provider. You can leave this unchecked.")

        submit_label = "Sign in" if auth_mode == "Login" else "Create account"
        submit = st.form_submit_button(submit_label, use_container_width=True, type="primary")
        if submit:
            if not email or not password:
                st.error("Please enter both email address and password.")
            elif auth_mode == "Register Account" and (not profile.get("full_name") or not profile.get("username") or not profile.get("organisation")):
                st.error("Please complete your name, username and institution/company fields.")
            elif auth_mode == "Register Account" and not profile.get("phone_number"):
                st.error("Please enter a mobile number. You can manage messaging preferences later.")
            else:
                success, response = run_async_task(
                    process_authentication, auth_mode, email, password, profile
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
    user_data = st.session_state.user_info or {"username": "Engineer", "full_name": "Engineer", "company": "", "account_type": "professional"}
    company_display = user_data.get("company") or ("Independent" if user_data.get("account_type") == "professional" else "Student")
    profile_name = html.escape(str(user_data.get("full_name") or user_data.get("username") or "Engineer"))
    account_label = "Tertiary Student" if user_data.get("account_type") == "student" else "Professional"
    company_display = html.escape(str(company_display))
    st.markdown(
        f"""
        <div class="main-header" style="margin-top:0.35rem;">PetroNexa</div>
        <div class="sub-header" style="margin-bottom:0.4rem; padding-bottom:0.5rem;">
            <i class="fas fa-user-circle"></i> {profile_name} ({account_label})
            &nbsp;·&nbsp;
            <i class="fas fa-building"></i> {company_display}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================
# ENGINEERING DISCIPLINE ROUTER
# ============================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=34)
    st.markdown("### PetroNexa Engineering")
    discipline = st.radio(
        "Engineering Discipline",
        ["Drilling Engineering", "Reservoir Engineering"],
        key="engineering_discipline",
    )

if discipline == "Drilling Engineering":
    drilling_controls = render_drilling_sidebar()
    render_drilling_workspace(drilling_controls, user_data)
else:
    with st.sidebar:
        st.markdown('<div class="sidebar-heading">Reservoir Workspace</div>', unsafe_allow_html=True)
        st.caption("Reservoir calculations are isolated from the drilling hydraulics workspace.")
        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    render_reservoir_workspace()

st.markdown('<div class="footer">© 2026 PetroNexa · Petroleum Engineering Platform</div>', unsafe_allow_html=True)
