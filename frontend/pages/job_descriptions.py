import streamlit as st

from frontend import api_client
from frontend.auth_state import require_auth
from frontend.components.jd_editor import render_jd_editor


def render():
    require_auth()
    st.header("Job Descriptions")

    render_jd_editor()

    st.divider()
    st.subheader("Your Job Descriptions")

    jds = api_client.list_jds()
    if not jds:
        st.info("No job descriptions yet. Create one above.")
        return

    for jd in jds:
        with st.expander(f"📋 {jd['title']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Created:** {jd['created_at'][:19]}")

                if jd.get("required_skills"):
                    st.markdown(f"**Required Skills:** {', '.join(jd['required_skills'])}")
                if jd.get("preferred_skills"):
                    st.markdown(f"**Preferred Skills:** {', '.join(jd['preferred_skills'])}")
                if jd.get("min_experience_years"):
                    st.markdown(f"**Min Experience:** {jd['min_experience_years']} years")
                if jd.get("keywords"):
                    st.markdown(f"**Keywords:** {', '.join(jd['keywords'])}")

                if jd.get("scoring_weights"):
                    w = jd["scoring_weights"]
                    st.markdown(
                        f"**Weights:** Skills {w.get('skills', 0.4):.0%} | "
                        f"Exp {w.get('experience', 0.3):.0%} | "
                        f"Projects {w.get('projects', 0.2):.0%} | "
                        f"Keywords {w.get('keywords', 0.1):.0%}"
                    )

            with col2:
                if st.button("🗑️ Delete", key=f"del_jd_{jd['id']}", use_container_width=True):
                    try:
                        api_client.delete_jd(jd["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

            with st.expander("Raw JD Text"):
                st.text(jd["raw_text"][:2000])
