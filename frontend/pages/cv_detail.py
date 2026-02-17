import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.cv_table import render_cv_detail_inline


def render():
    require_auth()
    st.header("CV Detail")

    cv_id = st.session_state.get("selected_cv_id")
    if not cv_id:
        st.info("Select a CV from the CV Management page.")
        return

    render_cv_detail_inline(cv_id)
