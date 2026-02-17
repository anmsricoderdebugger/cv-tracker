import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.cv_table import render_cv_table


def render():
    require_auth()
    st.header("CV Management")

    folders = api_client.list_folders()
    if not folders:
        st.info("Connect a folder first from the Dashboard.")
        return

    folder_options = {f"{f['label'] or f['folder_path']}": f["id"] for f in folders}
    selected_label = st.selectbox("Select Folder", options=list(folder_options.keys()))

    if selected_label:
        folder_id = folder_options[selected_label]

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔍 Scan for New CVs", use_container_width=True):
                with st.spinner("Scanning..."):
                    try:
                        result = api_client.scan_folder(folder_id)
                        st.success(
                            f"{result['new']} new, {result['modified']} modified, "
                            f"{result['skipped']} unchanged"
                        )
                        if result.get("task_id"):
                            st.info("Processing started in background...")
                            st.session_state[f"task_{folder_id}"] = result["task_id"]
                    except Exception as e:
                        st.error(f"Scan failed: {e}")

        # Check for in-progress task
        task_key = f"task_{folder_id}"
        if task_key in st.session_state:
            from frontend.components.progress_bar import render_progress
            render_progress(st.session_state[task_key], "CV Processing")
            del st.session_state[task_key]

        st.divider()
        render_cv_table(folder_id=folder_id)
