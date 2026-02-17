import time

import streamlit as st

from frontend import api_client


def render_progress(task_id: str, label: str = "Processing"):
    progress_bar = st.progress(0, text=f"{label}...")
    status_text = st.empty()

    while True:
        progress = api_client.get_progress(task_id)
        if not progress or progress.get("status") == "unknown":
            status_text.warning("Task status unknown.")
            break

        total = progress.get("total", 1) or 1
        current = progress.get("current", 0)
        pct = min(current / total, 1.0)
        progress_bar.progress(pct, text=progress.get("message", f"{label}..."))

        if progress.get("status") == "completed":
            progress_bar.progress(1.0, text="Complete!")
            status_text.success(f"{label} complete: {current}/{total}")
            break

        time.sleep(2)
