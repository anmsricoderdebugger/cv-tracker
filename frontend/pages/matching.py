import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.export_buttons import render_export_buttons
from frontend.components.leaderboard import render_leaderboard
from frontend.components.progress_bar import render_progress


def render():
    require_auth()
    st.header("Matching & Leaderboard")

    jds = api_client.list_jds()
    if not jds:
        st.info("Create a Job Description first.")
        return

    jd_options = {jd["title"]: jd["id"] for jd in jds}
    selected_title = st.selectbox("Select Job Description", options=list(jd_options.keys()))

    if not selected_title:
        return

    jd_id = jd_options[selected_title]

    # Show JD summary
    jd = api_client.get_jd(jd_id)
    with st.expander("JD Details", expanded=False):
        if jd.get("required_skills"):
            st.markdown(f"**Required Skills:** {', '.join(jd['required_skills'])}")
        if jd.get("min_experience_years"):
            st.markdown(f"**Min Experience:** {jd['min_experience_years']} years")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 Run Matching", use_container_width=True):
            try:
                result = api_client.trigger_matching(jd_id)
                st.success(f"Matching started for {result['total_cvs']} CVs")
                render_progress(result["task_id"], "Matching")
                st.rerun()
            except Exception as e:
                st.error(f"Matching failed: {e}")

    st.divider()

    render_leaderboard(jd_id)

    st.divider()
    render_export_buttons(jd_id)
