import streamlit as st


def is_authenticated() -> bool:
    return "token" in st.session_state and st.session_state.token is not None


def set_auth(token: str, user: dict):
    st.session_state.token = token
    st.session_state.user = user


def clear_auth():
    st.session_state.pop("token", None)
    st.session_state.pop("user", None)


def get_user() -> dict | None:
    return st.session_state.get("user")


def require_auth():
    if not is_authenticated():
        st.warning("Please log in to continue.")
        st.stop()
