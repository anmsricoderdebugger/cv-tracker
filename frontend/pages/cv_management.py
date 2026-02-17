import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.cv_table import render_cv_table


def render():
    require_auth()
    st.header("CV Management")

    folders = api_client.list_folders()
    if not folders:
        st.info("Create a collection first from the Dashboard.")
        return

    folder_options = {f['label']: f["id"] for f in folders}
    selected_label = st.selectbox("Select Collection", options=list(folder_options.keys()))

    if selected_label:
        folder_id = folder_options[selected_label]

        # Upload section
        uploaded_files = st.file_uploader(
            "Upload CVs (PDF or DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key=f"cv_upload_{folder_id}",
        )

        if uploaded_files:
            if st.button("Upload & Process", use_container_width=True, type="primary"):
                file_data = [(f.name, f.getvalue()) for f in uploaded_files]
                with st.spinner(f"Uploading {len(file_data)} file(s)..."):
                    try:
                        result = api_client.upload_cvs(folder_id, file_data)
                        st.success(
                            f"{result['new']} new CVs uploaded, "
                            f"{result['skipped']} duplicates skipped"
                        )
                        if result.get("task_id"):
                            st.info("Processing started in background...")
                            st.session_state[f"task_{folder_id}"] = result["task_id"]
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

        # Check for in-progress task
        task_key = f"task_{folder_id}"
        if task_key in st.session_state:
            from frontend.components.progress_bar import render_progress
            render_progress(st.session_state[task_key], "CV Processing")
            del st.session_state[task_key]

        st.divider()
        render_cv_table(folder_id=folder_id)
