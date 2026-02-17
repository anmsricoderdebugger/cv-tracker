import streamlit as st

from frontend import api_client


def render_export_buttons(jd_id: str):
    st.subheader("Export Results")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export CSV", use_container_width=True):
            try:
                data = api_client.export_leaderboard(jd_id, "csv")
                st.download_button(
                    "Download CSV",
                    data,
                    file_name="leaderboard.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col2:
        if st.button("📥 Export Excel", use_container_width=True):
            try:
                data = api_client.export_leaderboard(jd_id, "xlsx")
                st.download_button(
                    "Download Excel",
                    data,
                    file_name="leaderboard.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col3:
        if st.button("📥 Export PDF", use_container_width=True):
            try:
                data = api_client.export_leaderboard(jd_id, "pdf")
                st.download_button(
                    "Download PDF",
                    data,
                    file_name="leaderboard.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Export failed: {e}")
