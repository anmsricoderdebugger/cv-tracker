import streamlit as st

from frontend.auth_state import clear_auth, get_user, is_authenticated


def render_sidebar():
    with st.sidebar:
        st.title("CV Tracker")
        st.caption("Smart ATS Matcher")

        if is_authenticated():
            user = get_user()
            st.write(f"Logged in as **{user.get('full_name', '')}**")
            st.divider()

            page = st.radio(
                "Navigation",
                ["Dashboard", "Job Descriptions", "CV Management", "Matching & Leaderboard"],
                label_visibility="collapsed",
            )

            st.divider()
            if st.button("Logout", use_container_width=True):
                clear_auth()
                st.rerun()

            return page
        return None
