# src/ui/generate_tab.py
import streamlit as st
from src.tools.job_store import list_jobs, get_job, get_settings
from src.models.schemas import GenerationRequest, JobStatus
from src.agents.orchestrator import run_orchestrator
from src.tools.output_writer import write_local, push_confluence, push_jira


def render(user_id: int):
    st.header("Generate Artefacts")
    settings = get_settings(user_id)
    jobs = [j for j in list_jobs(user_id) if j.status == JobStatus.READY]

    if not jobs:
        st.info("No ready jobs. Upload and ingest a file first.")
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
    confluence_space = st.text_input("Confluence space key", value="ENG") if push_cf else None
    push_jira_flag = st.checkbox("Create Jira stories", value=False)
    jira_project = st.text_input("Jira project key", value="PROJ") if push_jira_flag else None

    if st.button("Generate", type="primary"):
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
            return

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
        st.success(f"Generated {len(outputs)} artefact(s).")

        if push_cf and settings.confluence_url:
            errors = push_confluence(outputs, confluence_space,
                                     settings.confluence_url, settings.confluence_token)
            for e in errors:
                st.warning(f"Confluence: {e}")

        if push_jira_flag and "user_story" in outputs and settings.jira_url:
            errors = push_jira(outputs["user_story"], jira_project,
                               settings.jira_url, settings.jira_token)
            for e in errors:
                st.warning(f"Jira: {e}")

        for name, output in outputs.items():
            st.download_button(
                label=f"Download {name}.md",
                data=output.content,
                file_name=f"{name}.md",
                mime="text/markdown",
                key=f"dl_{job_id}_{name}",
            )
