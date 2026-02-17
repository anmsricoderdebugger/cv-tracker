import streamlit as st
import pandas as pd

from frontend import api_client


def fit_color(status: str) -> str:
    return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(status, "⚪")


def render_leaderboard(jd_id: str):
    entries = api_client.get_leaderboard(jd_id)
    if not entries:
        st.info("No match results yet. Run matching first.")
        return

    rows = []
    for e in entries:
        rows.append({
            "Rank": e["rank"],
            "Candidate": e["candidate_name"],
            "Score": f"{e['overall_score']:.1f}%",
            "Fit": f"{fit_color(e['fit_status'])} {e['fit_status'].title()}",
            "Skills": f"{e['skills_score']:.0f}",
            "Exp": f"{e['experience_score']:.0f}",
            "Projects": f"{e['projects_score']:.0f}",
            "Keywords": f"{e['keywords_score']:.0f}",
            "Strengths": "; ".join(e.get("strengths", [])[:2]),
            "Gaps": "; ".join(e.get("gaps", [])[:2]),
            "_cv_file_id": e["cv_file_id"],
            "_explanation": e.get("explanation", ""),
            "_matched_skills": e.get("matched_skills", []),
            "_missing_skills": e.get("missing_skills", []),
        })

    df = pd.DataFrame(rows)
    display_cols = ["Rank", "Candidate", "Score", "Fit", "Skills", "Exp", "Projects", "Keywords", "Strengths", "Gaps"]

    selected = st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if selected and selected.selection and selected.selection.rows:
        row_idx = selected.selection.rows[0]
        entry = rows[row_idx]
        render_match_detail(entry)


def render_match_detail(entry: dict):
    st.divider()
    st.subheader(f"Match Detail: {entry['Candidate']}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Score", entry["Score"])
    with col2:
        st.metric("Skills", entry["Skills"])
    with col3:
        st.metric("Experience", entry["Exp"])
    with col4:
        st.metric("Projects", entry["Projects"])

    if entry.get("_matched_skills"):
        st.markdown("**Matched Skills:**")
        st.success(", ".join(entry["_matched_skills"]))

    if entry.get("_missing_skills"):
        st.markdown("**Missing Skills:**")
        st.error(", ".join(entry["_missing_skills"]))

    if entry.get("_explanation"):
        st.markdown("**Explanation:**")
        st.info(entry["_explanation"])

    # Link to full CV detail
    if st.button("View Full CV", key=f"view_cv_{entry['_cv_file_id']}"):
        st.session_state["selected_cv_id"] = entry["_cv_file_id"]
        st.session_state["page_override"] = "CV Management"
        st.rerun()
