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

# src/ui/generate_tab.py
import io
import zipfile

import streamlit as st

from src.tools.job_store import list_jobs, get_job, get_settings
from src.models.schemas import GenerationRequest, JobStatus
from src.agents.orchestrator import run_orchestrator
from src.tools.output_writer import write_local, push_confluence, push_jira


_STATE_KEY = "generated_outputs"  # session_state[_STATE_KEY][job_id] = {name: content}


def _ready_jobs(user_id: int):
    return [j for j in list_jobs(user_id) if j.status == JobStatus.READY]


def _store_outputs(job_id: str, outputs: dict) -> None:
    bucket = st.session_state.setdefault(_STATE_KEY, {})
    bucket[job_id] = {name: out.content for name, out in outputs.items()}


def _stored_outputs(job_id: str) -> dict:
    return st.session_state.get(_STATE_KEY, {}).get(job_id, {})


def _clear_outputs(job_id: str) -> None:
    bucket = st.session_state.get(_STATE_KEY, {})
    bucket.pop(job_id, None)


def _zip_bytes(name_to_content: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in name_to_content.items():
            zf.writestr(f"{name}.md", content)
    return buf.getvalue()


def render(user_id: int):
    st.header("Generate Artefacts")
    settings = get_settings(user_id)

    jobs = _ready_jobs(user_id)
    if not jobs:
        st.info("No ready jobs yet. Upload a file and wait for ingest to finish.")
        return

    job_options = {f"{j.filename} ({j.id[:8]}…)": j.id for j in jobs}
    selected_label = st.selectbox("Select job", list(job_options.keys()))
    job_id = job_options[selected_label]

    st.subheader("Artefacts to generate")
    col1, col2 = st.columns(2)
    gen_mom = col1.checkbox("Minutes of Meeting (MoM)", value=True)
    gen_kt = col1.checkbox("KT Document")
    gen_runbook = col2.checkbox("Runbook Update")
    gen_stories = col2.checkbox("User Stories")
    gen_translate = col2.checkbox("Translate outputs")
    target_lang = None
    if gen_translate:
        target_lang = st.selectbox("Target language", ["FR", "DE", "SV", "ZH", "JP"])

    st.subheader("Output destinations")
    push_cf = st.checkbox("Push to Confluence", value=False)
    confluence_space = None
    confluence_target = None
    if push_cf:
        confluence_space = st.text_input("Confluence space key", value="ENG")
        confluence_target = st.text_input(
            "Target page (optional — title or numeric page ID)",
            value="",
            help=(
                "Leave blank to publish one page per artefact at the space root.\n"
                "Set this to merge ALL selected artefacts into a single existing "
                "page (created if it doesn't exist). Accepts a page title or a "
                "numeric Confluence page ID."
            ),
        )
        if confluence_target:
            st.caption(
                "📄 Single-page mode — all selected artefacts will be merged into "
                f"`{confluence_target}` (replacing its current contents)."
            )
    push_jira_flag = st.checkbox("Create Jira stories", value=False)
    jira_project = st.text_input("Jira project key", value="PROJ") if push_jira_flag else None

    generate_clicked = st.button("Generate", type="primary")

    if generate_clicked:
        artefacts = []
        if gen_mom:
            artefacts.append("mom")
        if gen_kt:
            artefacts.append("kt_doc")
        if gen_runbook:
            artefacts.append("runbook")
        if gen_stories:
            artefacts.append("user_story")
        if gen_translate:
            artefacts.append("translation")

        if not artefacts:
            st.warning("Select at least one artefact.")
        else:
            req = GenerationRequest(
                job_id=job_id, user_id=user_id, artefacts=artefacts,
                target_lang=target_lang,
                push_confluence=push_cf, push_jira=push_jira_flag,
                confluence_space=confluence_space, jira_project=jira_project,
                provider=settings.provider, model_id=settings.model,
            )

            job = get_job(job_id)
            with st.spinner("Running agents…"):
                outputs = run_orchestrator(req, job.normalised_text)

            write_local(job_id=job_id, outputs=outputs)
            _store_outputs(job_id, outputs)
            st.success(f"Generated {len(outputs)} artefact(s).")

            if push_cf and settings.confluence_url:
                errors = push_confluence(outputs, confluence_space,
                                         settings.confluence_url, settings.confluence_token,
                                         email=settings.confluence_email,
                                         target_page=(confluence_target or None))
                for e in errors:
                    st.warning(f"Confluence: {e}")

            if push_jira_flag and "user_story" in outputs and settings.jira_url:
                errors = push_jira(outputs["user_story"], jira_project,
                                   settings.jira_url, settings.jira_token,
                                   email=settings.jira_email)
                for e in errors:
                    st.warning(f"Jira: {e}")

    # ── Persistent download panel ────────────────────────────────────────────
    # Rendered from session_state so individual download clicks don't erase
    # the list. Outputs only clear when the user explicitly clicks Clear.
    stored = _stored_outputs(job_id)
    if stored:
        st.divider()
        st.subheader(f"Generated artefacts ({len(stored)})")

        top_l, top_r = st.columns([1, 1])
        top_l.download_button(
            label=f"⬇️  Download all ({len(stored)}) as ZIP",
            data=_zip_bytes(stored),
            file_name=f"artefacts_{job_id[:8]}.zip",
            mime="application/zip",
            key=f"dl_zip_{job_id}",
            type="primary",
        )
        if top_r.button("Clear generated artefacts", key=f"clear_{job_id}"):
            _clear_outputs(job_id)
            st.rerun()

        for name, content in stored.items():
            with st.expander(f"📄  {name}.md", expanded=False):
                st.download_button(
                    label=f"Download {name}.md",
                    data=content,
                    file_name=f"{name}.md",
                    mime="text/markdown",
                    key=f"dl_{job_id}_{name}",
                )
                st.markdown(content)
