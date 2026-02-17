import streamlit as st

from frontend import api_client


def render_jd_editor():
    st.subheader("Create Job Description")

    method = st.radio("Input method", ["Paste Text", "Upload File"], horizontal=True)

    if method == "Paste Text":
        with st.form("jd_text_form"):
            title = st.text_input("Job Title")
            raw_text = st.text_area("Job Description", height=300, placeholder="Paste the full job description here...")

            st.markdown("**Scoring Weights** (optional - defaults: Skills 40%, Experience 30%, Projects 20%, Keywords 10%)")
            use_custom = st.checkbox("Customize scoring weights")

            skills_w = 0.4
            exp_w = 0.3
            proj_w = 0.2
            kw_w = 0.1

            if use_custom:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    skills_w = st.slider("Skills", 0.0, 1.0, 0.4, 0.05)
                with col2:
                    exp_w = st.slider("Experience", 0.0, 1.0, 0.3, 0.05)
                with col3:
                    proj_w = st.slider("Projects", 0.0, 1.0, 0.2, 0.05)
                with col4:
                    kw_w = st.slider("Keywords", 0.0, 1.0, 0.1, 0.05)

                total = skills_w + exp_w + proj_w + kw_w
                if abs(total - 1.0) > 0.01:
                    st.warning(f"Weights sum to {total:.2f}, must equal 1.0")

            submitted = st.form_submit_button("Create JD", use_container_width=True)

            if submitted:
                if not title or not raw_text:
                    st.error("Title and description are required")
                    return
                weights = None
                if use_custom:
                    weights = {"skills": skills_w, "experience": exp_w, "projects": proj_w, "keywords": kw_w}
                try:
                    jd = api_client.create_jd(title, raw_text, weights)
                    st.success(f"JD created: {jd['title']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create JD: {e}")

    else:
        title = st.text_input("Job Title", key="upload_title")
        uploaded_file = st.file_uploader("Upload JD (PDF or DOCX)", type=["pdf", "docx"])
        if st.button("Upload & Create JD", use_container_width=True):
            if not title or not uploaded_file:
                st.error("Title and file are required")
                return
            try:
                jd = api_client.upload_jd_file(title, uploaded_file.getvalue(), uploaded_file.name)
                st.success(f"JD created: {jd['title']}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create JD: {e}")
