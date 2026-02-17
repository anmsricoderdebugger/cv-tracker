import streamlit as st

st.set_page_config(
    page_title="CV Tracker - Smart ATS Matcher",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.auth_state import is_authenticated
from frontend.components.sidebar import render_sidebar
from frontend.pages import cv_detail, cv_management, dashboard, job_descriptions, login, matching

# Check for page override from other components
page_override = st.session_state.pop("page_override", None)

page = render_sidebar()

if not is_authenticated():
    login.render()
else:
    active_page = page_override or page

    if active_page == "Dashboard":
        dashboard.render()
    elif active_page == "Job Descriptions":
        job_descriptions.render()
    elif active_page == "CV Management":
        cv_management.render()
    elif active_page == "Matching & Leaderboard":
        matching.render()
    else:
        dashboard.render()
