# src/ui/history_tab.py
import streamlit as st
from src.tools.job_store import list_jobs
from src.config import JOBS_DIR


def render(user_id: int):
    st.header("Job History")
    jobs = list_jobs(user_id)
    if not jobs:
        st.info("No jobs yet.")
        return
    for j in jobs:
        icon = {"QUEUED": "⏳", "PROCESSING": "🔄", "READY": "✅", "FAILED": "❌"}.get(j.status, "?")
        with st.expander(f"{icon} {j.filename} — {j.created_at.strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"**Job ID:** `{j.id}`")
            st.write(f"**Status:** {j.status}")
            st.write(f"**Input type:** {j.input_type}")
            if j.error_msg:
                st.error(f"Error: {j.error_msg}")
            if j.normalised_text:
                st.text_area("Text preview", j.normalised_text[:500] + "…", height=120)
            job_dir = JOBS_DIR / j.id
            if job_dir.exists():
                files = list(job_dir.glob("*.md"))
                if files:
                    st.write("**Generated artefacts:**")
                    for f in files:
                        st.download_button(
                            label=f.name,
                            data=f.read_text(encoding="utf-8"),
                            file_name=f.name,
                            mime="text/markdown",
                            key=f"dl_{j.id}_{f.name}",
                        )
