import os

import streamlit as st

from frontend import api_client
from frontend.auth_state import set_auth

# Backend API root (without /api/v1 suffix) — used for OAuth redirect links
_API_ROOT = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1").removesuffix("/api/v1")


def render_login_form():
    st.title("CV Tracker & Smart ATS Matcher")
    st.subheader("Sign in to continue")

    # -----------------------------------------------------------------------
    # Google SSO button
    # -----------------------------------------------------------------------
    google_login_url = f"{_API_ROOT}/api/v1/auth/google/login"
    st.markdown(
        f"""
        <a href="{google_login_url}" target="_self" style="text-decoration:none;">
            <div style="
                display:flex; align-items:center; justify-content:center; gap:10px;
                background:#ffffff; color:#3c4043; border:1px solid #dadce0;
                border-radius:4px; padding:10px 24px; font-size:15px; font-weight:500;
                cursor:pointer; width:100%; box-sizing:border-box;
                font-family:'Google Sans',Roboto,Arial,sans-serif;
            ">
                <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#4285F4"
                        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209
                        1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567
                        2.684-3.874 2.684-6.615z"/>
                    <path fill="#34A853"
                        d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86
                        -3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997
                        8.997 0 0 0 9 18z"/>
                    <path fill="#FBBC05"
                        d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961
                        H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957
                        4.039l3.007-2.332z"/>
                    <path fill="#EA4335"
                        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891
                        11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964
                        6.293C4.672 4.166 6.656 3.58 9 3.58z"/>
                </svg>
                Sign in with Google
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("**Or sign in with email**")

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
