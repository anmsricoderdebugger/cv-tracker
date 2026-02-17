import streamlit as st

from frontend import api_client


def render_folder_picker():
    st.subheader("Connect Folder")

    with st.form("folder_form"):
        folder_path = st.text_input(
            "Folder Path",
            placeholder="/path/to/cv/folder",
            help="Enter the full path to the folder containing CVs (PDF/DOCX)"
        )
        label = st.text_input("Label (optional)", placeholder="e.g. Senior Dev Candidates")
        submitted = st.form_submit_button("Connect Folder", use_container_width=True)

        if submitted:
            if not folder_path:
                st.error("Folder path is required")
                return
            try:
                folder = api_client.create_folder(folder_path, label or None)
                st.success(f"Folder connected: {folder['label']}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to connect folder: {e}")


def render_folder_list():
    st.subheader("Monitored Folders")

    folders = api_client.list_folders()
    if not folders:
        st.info("No folders connected yet. Add one above.")
        return

    for folder in folders:
        with st.expander(f"📁 {folder['label'] or folder['folder_path']}", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(f"Path: {folder['folder_path']}")
                if folder["last_scanned_at"]:
                    st.text(f"Last scanned: {folder['last_scanned_at'][:19]}")
                else:
                    st.text("Not scanned yet")
            with col2:
                if st.button("🔍 Scan", key=f"scan_{folder['id']}", use_container_width=True):
                    with st.spinner("Scanning folder..."):
                        try:
                            result = api_client.scan_folder(folder["id"])
                            st.success(
                                f"Found {result['total_on_disk']} CVs: "
                                f"{result['new']} new, {result['modified']} modified, "
                                f"{result['skipped']} unchanged"
                            )
                            if result.get("task_id"):
                                st.info(f"Processing task started: {result['task_id'][:8]}...")
                                st.session_state[f"task_{folder['id']}"] = result["task_id"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Scan failed: {e}")
            with col3:
                if st.button("🗑️ Remove", key=f"del_{folder['id']}", use_container_width=True):
                    try:
                        api_client.delete_folder(folder["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to remove: {e}")

            # Show folder status
            try:
                status = api_client.get_folder_status(folder["id"])
                if status["total_cvs"] > 0:
                    counts = status["status_counts"]
                    cols = st.columns(5)
                    with cols[0]:
                        st.metric("Total", status["total_cvs"])
                    with cols[1]:
                        st.metric("Processed", counts.get("processed", 0))
                    with cols[2]:
                        st.metric("New", counts.get("new", 0))
                    with cols[3]:
                        st.metric("Processing", counts.get("processing", 0))
                    with cols[4]:
                        st.metric("Errors", counts.get("error", 0))
            except Exception:
                pass
