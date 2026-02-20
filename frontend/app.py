import streamlit as st

st.set_page_config(
    page_title="CV Tracker - Smart ATS Matcher",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend import api_client
from frontend.auth_state import is_authenticated, set_auth
from frontend.components.sidebar import render_sidebar
from frontend.pages import cv_detail, cv_management, dashboard, job_descriptions, login, matching

# ---------------------------------------------------------------------------
# Handle Google OAuth2 SSO callback — token passed as ?token=... query param
# ---------------------------------------------------------------------------
_qp = st.query_params
if "token" in _qp and not is_authenticated():
    _sso_token = _qp["token"]
    try:
        _user = api_client.get_me(token=_sso_token)
        set_auth(_sso_token, _user)
    except Exception:
        st.error("Google sign-in failed. Please try again.")
    finally:
        st.query_params.clear()
    st.rerun()

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
