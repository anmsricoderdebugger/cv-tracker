import streamlit as st

from frontend import api_client
from frontend.auth_state import set_auth


def render_login_form():
    st.title("CV Tracker & Smart ATS Matcher")
    st.subheader("Sign in to continue")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields")
                    return
                try:
                    result = api_client.login(email, password)
                    token = result["access_token"]
                    user = api_client.get_me(token=token)
                    set_auth(token, user)
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab_signup:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not full_name or not email or not password:
                    st.error("Please fill in all fields")
                    return
                try:
                    result = api_client.signup(email, password, full_name)
                    token = result["access_token"]
                    user = api_client.get_me(token=token)
                    set_auth(token, user)
                    st.success("Account created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Signup failed: {e}")
