import streamlit as st

from frontend import api_client


def render_folder_picker():
    st.subheader("Create CV Collection")

    with st.form("folder_form"):
        label = st.text_input(
            "Collection Name",
            placeholder="e.g. Senior Dev Candidates",
            help="Give your CV collection a descriptive name",
        )
        submitted = st.form_submit_button("Create Collection", use_container_width=True)

        if submitted:
            if not label:
                st.error("Collection name is required")
                return
            try:
                folder = api_client.create_folder(label)
                st.success(f"Collection created: {folder['label']}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create collection: {e}")

    # Upload section - show if there are collections
    folders = api_client.list_folders()
    if folders:
        st.subheader("Upload CVs")

        folder_options = {f['label']: f['id'] for f in folders}
        selected_label = st.selectbox(
            "Select Collection",
            options=list(folder_options.keys()),
            key="upload_folder_select",
        )

        uploaded_files = st.file_uploader(
            "Upload CV files (PDF or DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="cv_uploader",
        )

        if uploaded_files and selected_label:
            if st.button("Upload & Process", use_container_width=True, type="primary"):
                folder_id = folder_options[selected_label]
                file_data = [(f.name, f.getvalue()) for f in uploaded_files]

                with st.spinner(f"Uploading {len(file_data)} file(s)..."):
                    try:
                        result = api_client.upload_cvs(folder_id, file_data)
                        st.success(
                            f"Uploaded: {result['new']} new, "
                            f"{result['skipped']} duplicates skipped"
                        )
                        if result.get("task_id"):
                            st.info("Processing started in background...")
                            st.session_state[f"task_{folder_id}"] = result["task_id"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")


def render_folder_list():
    st.subheader("CV Collections")

    folders = api_client.list_folders()
    if not folders:
        st.info("No collections yet. Create one above.")
        return

    for folder in folders:
        with st.expander(f"📁 {folder['label']}", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                if folder["last_scanned_at"]:
                    st.text(f"Last updated: {folder['last_scanned_at'][:19]}")
                else:
                    st.text("No CVs uploaded yet")
            with col2:
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
