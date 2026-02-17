import os

import httpx
import streamlit as st

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")


def _headers() -> dict:
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(resp: httpx.Response):
    if resp.status_code == 401:
        st.session_state.pop("token", None)
        st.session_state.pop("user", None)
        st.error("Session expired. Please log in again.")
        st.stop()
    resp.raise_for_status()
    if resp.status_code == 204:
        return None
    return resp.json()


def signup(email: str, password: str, full_name: str) -> dict:
    resp = httpx.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": password, "full_name": full_name})
    if resp.status_code >= 400:
        detail = resp.json().get("detail", "Signup failed")
        raise Exception(detail)
    return resp.json()


def login(email: str, password: str) -> dict:
    resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if resp.status_code >= 400:
        detail = resp.json().get("detail", "Login failed")
        raise Exception(detail)
    return resp.json()


def get_me(token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else _headers()
    resp = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
    if token:
        # Called during login/signup — raise normal exception instead of st.stop()
        resp.raise_for_status()
        return resp.json()
    return _handle_response(resp)


# Job Descriptions
def create_jd(title: str, raw_text: str, scoring_weights: dict | None = None) -> dict:
    body = {"title": title, "raw_text": raw_text}
    if scoring_weights:
        body["scoring_weights"] = scoring_weights
    resp = httpx.post(f"{BASE_URL}/jds/", json=body, headers=_headers())
    return _handle_response(resp)


def upload_jd_file(title: str, file_content: bytes, filename: str) -> dict:
    resp = httpx.post(
        f"{BASE_URL}/jds/upload",
        data={"title": title},
        files={"file": (filename, file_content)},
        headers=_headers(),
    )
    return _handle_response(resp)


def list_jds() -> list:
    resp = httpx.get(f"{BASE_URL}/jds/", headers=_headers())
    return _handle_response(resp)


def get_jd(jd_id: str) -> dict:
    resp = httpx.get(f"{BASE_URL}/jds/{jd_id}", headers=_headers())
    return _handle_response(resp)


def update_jd_weights(jd_id: str, weights: dict) -> dict:
    resp = httpx.put(f"{BASE_URL}/jds/{jd_id}/weights", json=weights, headers=_headers())
    return _handle_response(resp)


def delete_jd(jd_id: str):
    resp = httpx.delete(f"{BASE_URL}/jds/{jd_id}", headers=_headers())
    return _handle_response(resp)


# Folders
def create_folder(label: str, folder_path: str | None = None) -> dict:
    body = {"label": label}
    if folder_path:
        body["folder_path"] = folder_path
    resp = httpx.post(f"{BASE_URL}/folders/", json=body, headers=_headers())
    return _handle_response(resp)


def upload_cvs(folder_id: str, files: list[tuple[str, bytes]]) -> dict:
    multipart_files = [("files", (name, content)) for name, content in files]
    resp = httpx.post(
        f"{BASE_URL}/folders/{folder_id}/upload",
        files=multipart_files,
        headers=_headers(),
        timeout=300,
    )
    return _handle_response(resp)


def list_folders() -> list:
    resp = httpx.get(f"{BASE_URL}/folders/", headers=_headers())
    return _handle_response(resp)


def scan_folder(folder_id: str) -> dict:
    resp = httpx.post(f"{BASE_URL}/folders/{folder_id}/scan", headers=_headers(), timeout=120)
    return _handle_response(resp)


def get_folder_status(folder_id: str) -> dict:
    resp = httpx.get(f"{BASE_URL}/folders/{folder_id}/status", headers=_headers())
    return _handle_response(resp)


def delete_folder(folder_id: str):
    resp = httpx.delete(f"{BASE_URL}/folders/{folder_id}", headers=_headers())
    return _handle_response(resp)


# CVs
def list_cvs(folder_id: str | None = None, status: str | None = None) -> list:
    params = {}
    if folder_id:
        params["folder_id"] = folder_id
    if status:
        params["status"] = status
    resp = httpx.get(f"{BASE_URL}/cvs/", params=params, headers=_headers())
    return _handle_response(resp)


def get_cv_detail(cv_id: str) -> dict:
    resp = httpx.get(f"{BASE_URL}/cvs/{cv_id}", headers=_headers())
    return _handle_response(resp)


def get_progress(task_id: str) -> dict:
    resp = httpx.get(f"{BASE_URL}/cvs/progress/{task_id}", headers=_headers())
    return _handle_response(resp)


# Matching
def trigger_matching(jd_id: str, cv_file_ids: list[str] | None = None) -> dict:
    body = {"jd_id": jd_id}
    if cv_file_ids:
        body["cv_file_ids"] = cv_file_ids
    resp = httpx.post(f"{BASE_URL}/matching/", json=body, headers=_headers())
    return _handle_response(resp)


def get_leaderboard(jd_id: str) -> list:
    resp = httpx.get(f"{BASE_URL}/matching/leaderboard/{jd_id}", headers=_headers())
    return _handle_response(resp)


# Export
def export_leaderboard(jd_id: str, fmt: str = "csv") -> bytes:
    resp = httpx.post(
        f"{BASE_URL}/export/leaderboard/{jd_id}",
        json={"format": fmt},
        headers=_headers(),
        timeout=60,
    )
    if resp.status_code == 401:
        st.session_state.pop("token", None)
        st.error("Session expired.")
        st.stop()
    resp.raise_for_status()
    return resp.content
