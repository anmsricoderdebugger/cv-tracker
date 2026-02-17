import streamlit as st
import pandas as pd

from frontend import api_client


def render_cv_table(folder_id: str | None = None):
    cvs = api_client.list_cvs(folder_id=folder_id)
    if not cvs:
        st.info("No CVs found.")
        return

    STATUS_COLORS = {
        "new": "🔵",
        "processing": "🟡",
        "processed": "🟢",
        "modified": "🟠",
        "error": "🔴",
    }

    rows = []
    for cv in cvs:
        rows.append({
            "Status": f"{STATUS_COLORS.get(cv['status'], '⚪')} {cv['status'].title()}",
            "File Name": cv["file_name"],
            "Size (KB)": round(cv["file_size_bytes"] / 1024, 1) if cv.get("file_size_bytes") else "-",
            "Detected": cv["detected_at"][:19] if cv.get("detected_at") else "-",
            "Processed": cv["processed_at"][:19] if cv.get("processed_at") else "-",
            "id": cv["id"],
        })

    df = pd.DataFrame(rows)

    selected = st.dataframe(
        df.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if selected and selected.selection and selected.selection.rows:
        row_idx = selected.selection.rows[0]
        cv_id = rows[row_idx]["id"]
        st.session_state["selected_cv_id"] = cv_id
        render_cv_detail_inline(cv_id)


def render_cv_detail_inline(cv_id: str):
    try:
        detail = api_client.get_cv_detail(cv_id)
    except Exception as e:
        st.error(f"Failed to load CV detail: {e}")
        return

    st.divider()
    st.subheader(f"CV Detail: {detail['file_name']}")

    parsed = detail.get("parsed_cv")
    if not parsed:
        st.warning("This CV has not been parsed yet.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {parsed.get('candidate_name', 'Unknown')}")
        st.markdown(f"**Email:** {parsed.get('email', '-')}")
        st.markdown(f"**Phone:** {parsed.get('phone', '-')}")
        st.markdown(f"**Experience:** {parsed.get('total_experience_years', '-')} years")

    with col2:
        if parsed.get("skills"):
            st.markdown("**Skills:**")
            st.write(", ".join(parsed["skills"]))
        if parsed.get("tools"):
            st.markdown("**Tools:**")
            st.write(", ".join(parsed["tools"]))

    if parsed.get("summary"):
        st.markdown("**Summary:**")
        st.write(parsed["summary"])

    if parsed.get("experience"):
        st.markdown("**Experience:**")
        for exp in parsed["experience"]:
            st.markdown(f"- **{exp.get('title', '')}** at {exp.get('company', '')} ({exp.get('duration', '')})")

    if parsed.get("education"):
        st.markdown("**Education:**")
        for edu in parsed["education"]:
            st.markdown(f"- {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')} ({edu.get('year', '')})")

    if parsed.get("projects"):
        st.markdown("**Projects:**")
        for proj in parsed["projects"]:
            st.markdown(f"- **{proj.get('name', '')}**: {proj.get('description', '')}")
