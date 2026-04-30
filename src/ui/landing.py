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

# src/ui/landing.py
"""Public landing-page UI shared between the pre-login splash and the
post-login Home tab.

Two entry points:
  - ``render_hero()``      — title, tagline, key value prop
  - ``render_features()``  — feature grid (cards)
  - ``render_provider_strip()`` — a horizontal logo-strip-style block
"""
import streamlit as st


_CSS = """
<style>
.landing-hero {
    text-align: center;
    padding: 1.5rem 1rem 0.75rem 1rem;
    background: linear-gradient(135deg, rgba(31,78,121,0.10), rgba(31,78,121,0.0));
    border-radius: 14px;
    margin-bottom: 1rem;
}
.landing-hero h1 {
    font-size: 2.1rem;
    margin: 0 0 0.4rem 0;
    background: linear-gradient(90deg, #1F4E79, #4F86C6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.landing-hero .tagline {
    color: #555;
    font-size: 1.05rem;
    margin-bottom: 0.5rem;
}
.landing-hero .badges {
    margin-top: 0.4rem;
}
.landing-hero .badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    margin: 0.15rem;
    border-radius: 999px;
    background: rgba(31,78,121,0.10);
    color: #1F4E79;
    font-size: 0.78rem;
    font-weight: 500;
}
.section-title {
    text-align: center;
    font-size: 1.35rem;
    color: #1F4E79;
    margin: 1.6rem 0 0.7rem 0;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.section-rule {
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(31,78,121,0.45), transparent);
    margin: 0 auto 1.0rem auto;
    max-width: 240px;
}
</style>
"""


def _inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero():
    """Top hero: title, tagline, value-prop badges. Safe to call multiple times."""
    _inject_css()
    st.markdown(
        """
        <div class="landing-hero">
            <h1>📋 Meeting &amp; Document Intelligence Platform</h1>
            <div class="tagline">
                Turn meetings, recordings, and documents into structured
                artefacts you can search, share, and ship — locally or in the cloud.
            </div>
            <div class="badges">
                <span class="badge">🔒 Local-first</span>
                <span class="badge">🤖 Multi-agent</span>
                <span class="badge">☁️ AWS Bedrock</span>
                <span class="badge">🔍 RAG Search</span>
                <span class="badge">👥 Multi-tenant</span>
                <span class="badge">📤 Confluence + Jira</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_title(title: str):
    st.markdown(
        f'<div class="section-title">{title}</div>'
        '<div class="section-rule"></div>',
        unsafe_allow_html=True,
    )


def render_features():
    """The full feature catalogue, rendered as bordered card columns."""
    _inject_css()

    _section_title("What this platform does")

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        with st.container(border=True):
            st.markdown("### 📥 Ingestion")
            st.markdown(
                "- **Audio &amp; video transcription** via faster-Whisper "
                "(MP3, MP4, WAV, M4A, WebM, OGG)\n"
                "- **Document parsing** via docling (PDF, DOCX, PPTX) with "
                "an `unstructured` fallback\n"
                "- **Plain transcripts** (TXT, MD) accepted as-is\n"
                "- **Background pipeline** — uploads run async; UI auto-refreshes "
                "while jobs progress QUEUED → PROCESSING → READY\n"
                "- **Embeddings** in ChromaDB; auto-routes between Ollama "
                "(`nomic-embed-text`) and AWS Bedrock Titan based on provider"
            )

        with st.container(border=True):
            st.markdown("### 🔍 Search &amp; retrieval")
            st.markdown(
                "- **RAG search** across your ingested corpus with inline citations\n"
                "- **Per-user collections** — your documents are private by default\n"
                "- **Opt-in shared library** — promote chunks to the org-wide "
                "collection when you choose to contribute\n"
                "- **Source previews** with similarity scores"
            )

    with col_b:
        with st.container(border=True):
            st.markdown("### 🤖 Artefact generation (multi-agent)")
            st.markdown(
                "- **Minutes of Meeting (MoM)** — decisions, action items, "
                "next steps, blockers\n"
                "- **Knowledge Transfer Document** — overview, components, "
                "step-by-step procedures, gotchas\n"
                "- **Runbook Update** — problem, detection, investigation, "
                "resolution, escalation, post-incident — with `[NEW]` / `[UPDATED]` tagging\n"
                "- **User Stories** — Jira-ready, with acceptance criteria and subtasks\n"
                "- **Translation** — local Helsinki-NLP models (FR / DE / SV / ZH / JP)"
            )

        with st.container(border=True):
            st.markdown("### 📤 Output destinations")
            st.markdown(
                "- **Local Markdown** — every artefact saved to `data/jobs/{job_id}/`\n"
                "- **Confluence push** — artefacts published as pages under a configured space\n"
                "- **Jira tickets** — user stories opened as issues in a configured project\n"
                "- **Direct download** — Markdown + ZIP-bundle download from Generate / History tabs"
            )

    _section_title("Platform capabilities")

    cap_a, cap_b, cap_c = st.columns(3, gap="medium")
    with cap_a:
        with st.container(border=True):
            st.markdown("### 🔐 Multi-tenant")
            st.markdown(
                "- Bcrypt-authenticated users (streamlit-authenticator)\n"
                "- Private SQLite scope per user\n"
                "- Private ChromaDB collection per user\n"
                "- Optional org-wide shared library"
            )
    with cap_b:
        with st.container(border=True):
            st.markdown("### ☁️ Local-first by default")
            st.markdown(
                "- Zero paid API cost out of the box\n"
                "- Transcription, embeddings, LLM all run locally\n"
                "- Switchable to managed clouds without code change\n"
                "- Translation via local Helsinki-NLP models"
            )
    with cap_c:
        with st.container(border=True):
            st.markdown("### 🛠️ Operations")
            st.markdown(
                "- Real-time job status with 2-second auto-refresh\n"
                "- Cross-tab refresh when jobs complete\n"
                "- Per-job and bulk delete in Recent Jobs / History\n"
                "- Markdown + ZIP download for any artefact set\n"
                "- Graceful failure — local files always written first"
            )

    _section_title("LLM provider flexibility")
    with st.container(border=True):
        prov_a, prov_b, prov_c = st.columns(3, gap="medium")
        with prov_a:
            st.markdown("**☁️ AWS Bedrock**")
            st.caption("Claude Sonnet 4 / 3.5 / Haiku — temporary or long-lived AWS creds via `.env`.")
        with prov_b:
            st.markdown("**🦙 Ollama (local)**")
            st.caption("Llama 3.3 / 3.1, Mistral, Qwen 2.5. Default. Zero cost.")
        with prov_c:
            st.markdown("**🌐 Managed APIs**")
            st.caption("OpenAI, Google Gemini, OpenRouter, LM Studio, custom OpenAI-compatible.")

    _section_title("Get started")
    st.markdown(
        "<div style='text-align:center; color:#555; margin-bottom:1rem;'>"
        "Sign in above → drop a file in <b>Upload &amp; Ingest</b> → "
        "pick your provider in <b>Settings</b> → generate or search."
        "</div>",
        unsafe_allow_html=True,
    )
