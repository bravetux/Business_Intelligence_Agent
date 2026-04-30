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

# src/ui/settings_tab.py
import os
from urllib.parse import urlparse

import streamlit as st
from src.tools.job_store import get_settings, save_settings
from src.models.schemas import UserSettings
from src.tools.output_writer import list_confluence_spaces, list_jira_projects


def _is_atlassian_cloud(url: str) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return host.endswith("atlassian.net") or host.endswith("atlassian.com")

PROVIDERS = ["ollama", "aws", "lmstudio", "openrouter", "openai", "gemini", "custom"]
PROVIDER_MODELS = {
    "ollama": ["llama3.3:70b", "llama3.1:8b", "mistral:7b", "qwen2.5:72b"],
    "aws": [
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
    ],
    "lmstudio": ["local-model"],
    "openrouter": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "custom": ["custom-model"],
}

# Legacy aliases — older saved settings rows may still say "bedrock"
PROVIDER_ALIASES = {"bedrock": "aws"}


def _normalise_provider(name: str) -> str:
    return PROVIDER_ALIASES.get(name, name)


def _aws_env_status() -> dict:
    """Report whether each required AWS env var is set (without revealing values)."""
    keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "BEDROCK_MODEL_ID",
    ]
    return {k: bool(os.getenv(k)) for k in keys}


def render(user_id: int):
    st.header("Settings")
    s = get_settings(user_id)
    current_provider = _normalise_provider(s.provider)
    if current_provider not in PROVIDERS:
        current_provider = PROVIDERS[0]

    with st.form("settings_form"):
        st.subheader("LLM Provider")
        provider = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(current_provider))

        if provider == "aws":
            status = _aws_env_status()
            region_set = status["AWS_REGION"] or status["AWS_DEFAULT_REGION"]
            required_ok = all([
                status["AWS_ACCESS_KEY_ID"],
                status["AWS_SECRET_ACCESS_KEY"],
                region_set,
            ])
            msg_lines = [
                f"- AWS_ACCESS_KEY_ID: {'set' if status['AWS_ACCESS_KEY_ID'] else 'MISSING'}",
                f"- AWS_SECRET_ACCESS_KEY: {'set' if status['AWS_SECRET_ACCESS_KEY'] else 'MISSING'}",
                f"- AWS_SESSION_TOKEN: {'set (temporary credentials)' if status['AWS_SESSION_TOKEN'] else 'not set (long-lived credentials)'}",
                f"- AWS_REGION / AWS_DEFAULT_REGION: {'set' if region_set else 'MISSING'}",
                f"- BEDROCK_MODEL_ID override: {'set' if status['BEDROCK_MODEL_ID'] else 'not set (UI selection used)'}",
            ]
            (st.success if required_ok else st.warning)(
                "AWS Bedrock — credentials read from environment (.env):\n\n"
                + "\n".join(msg_lines)
            )

        model_options = PROVIDER_MODELS.get(provider, [s.model])
        model = st.selectbox("Model", model_options,
                             index=0 if s.model not in model_options else model_options.index(s.model))

        st.subheader("Translation")
        lang_options = ["EN", "FR", "DE", "SV", "ZH", "JP"]
        target_lang = st.selectbox("Default target language",
                                   lang_options, index=lang_options.index(s.target_lang))

        st.subheader("Document Sharing")
        share_to_org = st.checkbox("Share my documents with the org library", value=s.share_to_org)

        st.subheader("Confluence (optional)")
        confluence_url = st.text_input(
            "Confluence URL", value=s.confluence_url or "",
            help="Cloud: https://your-org.atlassian.net/wiki  •  "
                 "Server/DC: https://confluence.your-company.com",
        )
        cf_cloud = _is_atlassian_cloud(confluence_url)
        if confluence_url:
            st.caption(
                "🌥️ Atlassian Cloud detected — email + API token required."
                if cf_cloud else
                "🏢 Server / Data Center detected — Personal Access Token (PAT) only."
            )
        confluence_email = st.text_input(
            "Confluence email" + (" (required for Cloud)" if cf_cloud else " (ignored for Server/DC)"),
            value=s.confluence_email or "",
            disabled=not cf_cloud,
        )
        confluence_token = st.text_input(
            "Confluence token", value=s.confluence_token or "",
            type="password",
            help="Cloud: API token from id.atlassian.com.  Server/DC: PAT.  "
                 "Tip: you can paste 'email:token' here and the email field auto-fills.",
        )

        st.subheader("Jira (optional)")
        jira_url = st.text_input(
            "Jira URL", value=s.jira_url or "",
            help="Cloud: https://your-org.atlassian.net  •  Server/DC: https://jira.your-company.com",
        )
        jira_cloud = _is_atlassian_cloud(jira_url)
        if jira_url:
            st.caption(
                "🌥️ Atlassian Cloud detected — email + API token required."
                if jira_cloud else
                "🏢 Server / Data Center detected — Personal Access Token (PAT) only."
            )
        jira_email = st.text_input(
            "Jira email" + (" (required for Cloud)" if jira_cloud else " (ignored for Server/DC)"),
            value=s.jira_email or "",
            disabled=not jira_cloud,
        )
        jira_token = st.text_input(
            "Jira token", value=s.jira_token or "", type="password",
            help="Cloud: API token from id.atlassian.com.  Server/DC: PAT.",
        )

        if st.form_submit_button("Save Settings"):
            updated = UserSettings(
                user_id=user_id, provider=provider, model=model,
                confluence_url=confluence_url or None,
                confluence_email=confluence_email or None,
                confluence_token=confluence_token or None,
                jira_url=jira_url or None,
                jira_email=jira_email or None,
                jira_token=jira_token or None,
                target_lang=target_lang,
                share_to_org=share_to_org,
            )
            save_settings(updated)
            st.success("Settings saved.")

    # ── Connection tests ────────────────────────────────────────────────
    # Outside the form so they can be triggered without resubmitting Save.
    # They use the *currently saved* settings, so click Save first if you
    # just edited the URL/email/token.
    saved = get_settings(user_id)
    st.divider()
    st.subheader("Connection tests")
    st.caption(
        "Tests use the saved values — if you just edited a field above, click "
        "**Save Settings** first, then run the test."
    )

    test_cf, test_jira = st.columns(2)

    with test_cf:
        cf_btn = st.button(
            "Test Confluence",
            disabled=not saved.confluence_url or not saved.confluence_token,
            use_container_width=True,
        )
        if cf_btn:
            with st.spinner("Listing accessible spaces…"):
                try:
                    spaces = list_confluence_spaces(
                        saved.confluence_url,
                        saved.confluence_token,
                        saved.confluence_email,
                    )
                except Exception as e:
                    st.error(f"❌  Confluence connection failed: {e}")
                else:
                    if not spaces:
                        st.warning(
                            "✅ Authenticated, but **no spaces are visible** to "
                            "this account. Ask a Confluence admin to grant "
                            "you View / Add Page permission on the space you "
                            "need to publish to."
                        )
                    else:
                        st.success(
                            f"✅ Authenticated — {len(spaces)} space(s) accessible. "
                            "Copy a key from below into the Confluence space-key "
                            "field on the Generate Artefacts tab."
                        )
                        with st.expander("Accessible spaces", expanded=True):
                            for sp in spaces:
                                badge = (
                                    "👤 personal" if sp.get("type") == "personal"
                                    else "🌐 global"
                                )
                                st.write(f"- **`{sp['key']}`** — {sp['name']}  ·  {badge}")

    with test_jira:
        jira_btn = st.button(
            "Test Jira",
            disabled=not saved.jira_url or not saved.jira_token,
            use_container_width=True,
        )
        if jira_btn:
            with st.spinner("Listing accessible projects…"):
                try:
                    projects = list_jira_projects(
                        saved.jira_url,
                        saved.jira_token,
                        saved.jira_email,
                    )
                except Exception as e:
                    st.error(f"❌  Jira connection failed: {e}")
                else:
                    if not projects:
                        st.warning(
                            "✅ Authenticated, but **no projects are visible**. "
                            "Ask a Jira admin to grant you `Browse Projects` and "
                            "`Create Issues` permission on the target project."
                        )
                    else:
                        st.success(
                            f"✅ Authenticated — {len(projects)} project(s) accessible. "
                            "Copy a key from below into the Jira project-key field."
                        )
                        with st.expander("Accessible projects", expanded=True):
                            for p in projects:
                                st.write(f"- **`{p['key']}`** — {p['name']}")
