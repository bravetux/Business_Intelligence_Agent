# Business Intelligence Agent
# Copyright (C) 2026  B. Vignesh Kumar (Bravetux) <ic19939@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# src/ui/upload_tab.py
import streamlit as st
from pathlib import Path
from src.config import UPLOADS_DIR
from src.models.schemas import InputType, JobStatus
from src.tools.job_store import create_job, get_settings, list_jobs
from src.tools import job_lifecycle
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
                         file_path=dest, input_type=input_type, share_to_org=share,
                         llm_provider=settings.provider)
            st.success(f"Queued: **{uf.name}** — Job ID: `{job.id[:8]}…`")

    st.divider()
    st.subheader("Recent Jobs")
    _recent_jobs_panel(user_id)


_TERMINAL_STATUSES = {"READY", "FAILED"}


@st.fragment(run_every=2)
def _recent_jobs_panel(user_id: int):
    jobs = list_jobs(user_id)[:10]
    if not jobs:
        st.info("No jobs yet.")
        return

    # Detect transitions into terminal status since the last tick.
    prev_state_key = f"_jobs_prev_state_{user_id}"
    prev = st.session_state.get(prev_state_key, {})
    current = {j.id: j.status for j in jobs}
    became_terminal = any(
        current[jid] in _TERMINAL_STATUSES
        and prev.get(jid) not in _TERMINAL_STATUSES
        and jid in prev
        for jid in current
    )
    st.session_state[prev_state_key] = current

    pending = any(j.status not in _TERMINAL_STATUSES for j in jobs)
    for j in jobs:
        icon = {"QUEUED": "⏳", "PROCESSING": "🔄", "READY": "✅", "FAILED": "❌"}.get(j.status, "?")
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        col1.write(f"{icon} **{j.filename}**")
        col2.write(j.status)
        col3.write(j.created_at.strftime("%H:%M:%S"))
        # Per-job delete — only allowed when the job is in a terminal state
        # (deleting a PROCESSING job would race with the background thread).
        del_disabled = j.status not in _TERMINAL_STATUSES
        if col4.button(
            "🗑️", key=f"del_{j.id}", help="Delete job",
            disabled=del_disabled,
        ):
            if job_lifecycle.delete_job(j.id, user_id):
                st.session_state.get("generated_outputs", {}).pop(j.id, None)
                st.toast(f"Deleted {j.filename}", icon="🗑️")
                st.rerun()
        if j.status == "FAILED" and j.error_msg:
            st.error(f"Error: {j.error_msg}")
    if pending:
        st.caption("Auto-refreshing every 2s while jobs are in progress…")

    # If anything just finished, rerun the whole app so other tabs (Generate /
    # Search / History) pick up the new READY job. st.rerun() inside a fragment
    # reruns the parent script.
    if became_terminal:
        st.rerun()
