# src/ui/upload_tab.py
import streamlit as st
from pathlib import Path
from src.config import UPLOADS_DIR
from src.models.schemas import InputType, JobStatus
from src.tools.job_store import create_job, get_settings, list_jobs
from src.pipeline.ingest import start_ingest

_AUDIO_VIDEO_EXT = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"}
_DOC_EXT = {".pdf", ".docx", ".pptx"}


def _detect_input_type(filename: str) -> InputType:
    ext = Path(filename).suffix.lower()
    if ext in _AUDIO_VIDEO_EXT:
        return InputType.AUDIO_VIDEO
    if ext in _DOC_EXT:
        return InputType.DOCUMENT
    return InputType.TRANSCRIPT


def render(user_id: int):
    st.header("Upload & Ingest")
    st.write("Upload audio, video, transcript, or document files. Ingestion runs in the background.")

    settings = get_settings(user_id)
    uploaded = st.file_uploader(
        "Drop files here",
        type=["mp3", "mp4", "wav", "m4a", "webm", "ogg", "pdf", "docx", "pptx", "txt", "md"],
        accept_multiple_files=True,
    )
    share = st.checkbox("Add to shared org library", value=settings.share_to_org)

    if st.button("Start Ingest", disabled=not uploaded):
        for uf in uploaded:
            dest = UPLOADS_DIR / uf.name
            dest.write_bytes(uf.getbuffer())
            input_type = _detect_input_type(uf.name)
            job = create_job(user_id, uf.name, input_type)
            start_ingest(job_id=job.id, user_id=user_id,
                         file_path=dest, input_type=input_type, share_to_org=share)
            st.success(f"Queued: **{uf.name}** — Job ID: `{job.id[:8]}…`")

    st.divider()
    st.subheader("Recent Jobs")
    jobs = list_jobs(user_id)[:10]
    if not jobs:
        st.info("No jobs yet.")
        return
    for j in jobs:
        icon = {"QUEUED": "⏳", "PROCESSING": "🔄", "READY": "✅", "FAILED": "❌"}.get(j.status, "?")
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"{icon} **{j.filename}**")
        col2.write(j.status)
        col3.write(j.created_at.strftime("%H:%M:%S"))
        if j.status == "FAILED" and j.error_msg:
            st.error(f"Error: {j.error_msg}")
