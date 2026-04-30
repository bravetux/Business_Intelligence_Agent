# Business Intelligence Agent

A local-first **Meeting & Document Intelligence Platform**. Upload meeting recordings, transcripts, or documents, and the platform turns them into structured artefacts — Minutes of Meeting, Knowledge Transfer docs, Runbooks, and Jira-ready user stories — using a fleet of LLM-driven sub-agents. It also provides semantic search over everything you've ingested, with optional translation into 10 language pairs.

The default deployment runs **fully offline** against an Ollama-hosted LLM and a local Chroma vector store. AWS Bedrock, OpenAI, OpenRouter, Gemini, and LM Studio are supported as drop-in alternatives via a single setting.

---

## What it does

- **Ingest** audio/video (Whisper transcription), PDF/DOCX/PPTX (Docling + Unstructured), or plain text. Chunks and embeds the content, then stores it in Chroma for retrieval.
- **Generate** any combination of the following artefacts from one source document, in one click:
  - **Minutes of Meeting** — title, attendees, decisions, action items with owners and due dates, next steps, open questions.
  - **Knowledge Transfer Doc** — overview, system description, components, step-by-step procedures, gotchas, references.
  - **Runbook** — problem statement, detection criteria, investigation steps, resolution steps, escalation path, post-incident actions. Marks new content `[NEW]` and revised procedures `[UPDATED]`.
  - **User Stories** — Jira-ready, with acceptance criteria in Given/When/Then form and implementation subtasks.
  - **Translation** — runs on top of any other artefact. Supports EN ↔ SV / JP / ZH / DE / FR via local Helsinki-NLP MarianMT models.
- **Search** across all ingested content with semantic retrieval and an LLM-backed answer agent.
- **Push outputs** to local files, **Confluence**, or **Jira** via REST.
- **Track history** — every generation job is recorded in SQLite with timestamps, inputs, outputs, and user attribution.

---

## Architecture at a glance

```
┌────────────────────────┐
│  Streamlit UI (app.py) │  Tabs: Home · Upload · Generate · Search · History · Settings
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐     ┌──────────────────────────────┐
│  Orchestrator          │────▶│  Sub-agents (Strands Agents) │
│  (deterministic Python)│     │   MoM · KT · Runbook ·       │
│                        │     │   UserStory · Translation    │
└───────────┬────────────┘     └──────────────────────────────┘
            │
            ▼
┌────────────────────────┐     ┌──────────────────────────────┐
│  Output Writer         │────▶│  Local files / Confluence /  │
│                        │     │  Jira                        │
└────────────────────────┘     └──────────────────────────────┘

┌────────────────────────┐     ┌──────────────────────────────┐
│  Ingest Pipeline       │────▶│  Chroma vector store         │
│  (Whisper · Docling)   │     │  + SQLite metadata (jobs.db) │
└────────────────────────┘     └──────────────────────────────┘
```

Routing is deterministic Python — `src/agents/orchestrator.py` inspects `GenerationRequest.artefacts` and dispatches to the matching sub-agents. The LLM is only used inside each agent, never to decide which agent to run.

---

## Quick start (Windows)

The fastest path is the bundled `startup.bat`:

```bat
startup.bat
```

It performs eight checks and then launches the app:

1. Verifies Python 3.11+
2. Installs `uv` if missing
3. Creates `.env` from `.env.example` if missing
4. Runs `uv sync` for all dependencies
5. Checks Ollama is reachable and the required models (`llama3.3:70b`, `nomic-embed-text`) are pulled
6. Initialises `auth.yaml` and SQLite DB on first run, prompting for admin credentials
7. Frees port 8503 if held
8. Launches Streamlit at `http://localhost:8503`

Default credentials on a fresh install: **admin / changeme** — change them in **Settings** after first login.

### Manual setup (any OS)

```bash
# 1. Install uv (https://docs.astral.sh/uv/)
pip install uv

# 2. Clone and install
git clone https://github.com/bravetux/Business_Intelligence_Agent.git
cd Business_Intelligence_Agent
uv sync

# 3. Configure the LLM provider
cp .env.example .env       # edit if you want OpenAI/Bedrock/Gemini instead of Ollama

# 4. Initialise auth + DB (first run only)
uv run python -m src.tools.init_db --admin-user admin --admin-pass changeme

# 5. Launch
uv run streamlit run app.py --server.port 8503
```

---

## Configuration

Provider selection lives in `.env` and the **Settings** tab. Recognised providers:

| Provider     | Env var                      | Notes                                    |
|--------------|------------------------------|------------------------------------------|
| `ollama`     | `OLLAMA_HOST`                | Default. Fully offline.                  |
| `aws`        | `AWS_*`, `BEDROCK_MODEL_ID`  | Bedrock — supports STS / SSO tokens.     |
| `lmstudio`   | `LMSTUDIO_HOST`              | Local LM Studio server.                  |
| `openai`     | `OPENAI_API_KEY`             |                                          |
| `openrouter` | `OPENROUTER_API_KEY`         |                                          |
| `gemini`     | `GEMINI_API_KEY`             |                                          |

Optional integrations:

- **Confluence** — set `CONFLUENCE_URL` + `CONFLUENCE_TOKEN` to enable "Push to Confluence".
- **Jira** — set `JIRA_URL` + `JIRA_TOKEN` to enable "Push to Jira" for user-story artefacts.
- **Translation models** — first time you select a target language, run `python -m src.tools.setup_translation` to download the local MarianMT weights.

---

## Try it with the bundled samples

The `samples/` folder contains realistic input documents you can paste into the **Generate** tab to exercise each agent end-to-end without sourcing internal data:

| Sample                                          | Best paired with         |
|------------------------------------------------|--------------------------|
| `samples/meeting_sprint_planning_q2.md`         | Minutes of Meeting       |
| `samples/kt_session_payment_service_onboarding.md` | KT Doc                |
| `samples/incident_payment_service_outage.md`    | Runbook                  |
| `samples/product_discovery_saved_cards_feature.md` | User Stories          |

For translation, generate any of the above first, then re-run with a target language selected — the orchestrator appends translated variants (e.g. `mom_translated_FR`).

---

## Project layout

```
business_intelligent/
├── app.py                       # Streamlit entry point
├── startup.bat                  # 8-step launcher (Windows)
├── pyproject.toml               # uv-managed dependencies
├── src/
│   ├── agents/                  # Sub-agents + orchestrator + doc-search
│   ├── pipeline/                # Ingest pipeline (transcribe → chunk → embed)
│   ├── tools/                   # Provider, embedding, Chroma, job store, output writer
│   ├── ui/                      # One module per Streamlit tab
│   ├── models/schemas.py        # Pydantic schemas (GenerationRequest, AgentOutput, ...)
│   └── config.py                # Centralised settings + paths
├── templates/                   # Jinja2 templates for each artefact
├── samples/                     # Realistic input documents for each agent
├── docs/                        # Specs, plans, whitepapers
└── tests/                       # Pytest suites
```

---

## Running tests

```bash
uv run pytest
```

Unit tests cover the agents, orchestrator, ingest pipeline, and storage layer. Integration tests that hit Ollama or external APIs are skipped by default — run them manually when those services are reachable.

---

## Author

**B. Vignesh Kumar** (Bravetux) · ic19939@gmail.com

---

## License

Internal / proprietary unless otherwise specified by the repository owner.
