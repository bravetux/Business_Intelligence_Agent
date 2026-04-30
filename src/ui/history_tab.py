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

# src/ui/history_tab.py
import streamlit as st

from src.config import JOBS_DIR
from src.tools.job_store import list_jobs
from src.tools import job_lifecycle


_TERMINAL_STATUSES = {"READY", "FAILED"}


def render(user_id: int):
    st.header("Job History")
    jobs = list_jobs(user_id)
    if not jobs:
        st.info("No jobs yet.")
        return

    # ── Bulk actions ──────────────────────────────────────────────────────
    col_count, col_clear = st.columns([3, 2])
    col_count.caption(f"{len(jobs)} job(s) on record.")
    with col_clear.popover("🗑️  Clear all history", use_container_width=True):
        st.warning(
            "This will delete every job for your user, including:\n\n"
            "- SQLite job rows\n"
            "- Generated artefacts under `data/jobs/`\n"
            "- Embedded chunks in your ChromaDB collection\n\n"
            "Uploaded source files in `data/uploads/` are kept."
        )
        if st.button("Yes, delete everything", type="primary", key="confirm_clear_all"):
            removed = job_lifecycle.delete_all_jobs(user_id)
            st.session_state.pop("generated_outputs", None)
            st.toast(f"Cleared {removed} job(s).", icon="🧹")
            st.rerun()

    st.divider()

    # ── Per-job list ──────────────────────────────────────────────────────
    for j in jobs:
        icon = {"QUEUED": "⏳", "PROCESSING": "🔄", "READY": "✅", "FAILED": "❌"}.get(j.status, "?")
        with st.expander(f"{icon} {j.filename} — {j.created_at.strftime('%Y-%m-%d %H:%M')}"):
            top_l, top_r = st.columns([4, 1])
            top_l.write(f"**Job ID:** `{j.id}`")
            top_l.write(f"**Status:** {j.status}")
            top_l.write(f"**Input type:** {j.input_type}")

            del_disabled = j.status not in _TERMINAL_STATUSES
            del_help = (
                "Cannot delete while ingest is in progress."
                if del_disabled else "Delete this job and all its artefacts."
            )
            if top_r.button(
                "🗑️ Delete",
                key=f"hist_del_{j.id}",
                disabled=del_disabled,
                help=del_help,
                use_container_width=True,
            ):
                if job_lifecycle.delete_job(j.id, user_id):
                    st.session_state.get("generated_outputs", {}).pop(j.id, None)
                    st.toast(f"Deleted {j.filename}", icon="🗑️")
                    st.rerun()

            if j.error_msg:
                st.error(f"Error: {j.error_msg}")
            if j.normalised_text:
                st.text_area(
                    "Text preview",
                    j.normalised_text[:500] + "…",
                    height=120,
                    key=f"hist_text_{j.id}",
                )
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
