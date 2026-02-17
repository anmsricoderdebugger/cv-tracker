import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.folder_picker import render_folder_list, render_folder_picker


def render():
    require_auth()
    st.header("Dashboard")

    # Overview stats
    try:
        folders = api_client.list_folders()
        jds = api_client.list_jds()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Connected Folders", len(folders))
        with col2:
            st.metric("Job Descriptions", len(jds))
        with col3:
            total_cvs = 0
            for f in folders:
                try:
                    status = api_client.get_folder_status(f["id"])
                    total_cvs += status.get("total_cvs", 0)
                except Exception:
                    pass
            st.metric("Total CVs", total_cvs)
    except Exception as e:
        st.error(f"Failed to load overview: {e}")

    st.divider()
    render_folder_picker()
    st.divider()
    render_folder_list()
