# src/ui/settings_tab.py
import streamlit as st
from src.tools.job_store import get_settings, save_settings
from src.models.schemas import UserSettings

PROVIDERS = ["ollama", "bedrock", "lmstudio", "openrouter", "openai", "gemini", "custom"]
PROVIDER_MODELS = {
    "ollama": ["llama3.3:70b", "llama3.1:8b", "mistral:7b", "qwen2.5:72b"],
    "bedrock": ["anthropic.claude-3-5-sonnet-20241022-v2:0", "anthropic.claude-3-haiku-20240307-v1:0"],
    "lmstudio": ["local-model"],
    "openrouter": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
    "custom": ["custom-model"],
}


def render(user_id: int):
    st.header("Settings")
    s = get_settings(user_id)

    with st.form("settings_form"):
        st.subheader("LLM Provider")
        provider = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(s.provider))
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
        confluence_url = st.text_input("Confluence URL", value=s.confluence_url or "")
        confluence_token = st.text_input("Confluence token", value=s.confluence_token or "",
                                         type="password")

        st.subheader("Jira (optional)")
        jira_url = st.text_input("Jira URL", value=s.jira_url or "")
        jira_token = st.text_input("Jira token", value=s.jira_token or "", type="password")

        if st.form_submit_button("Save Settings"):
            updated = UserSettings(
                user_id=user_id, provider=provider, model=model,
                confluence_url=confluence_url or None,
                confluence_token=confluence_token or None,
                jira_url=jira_url or None,
                jira_token=jira_token or None,
                target_lang=target_lang,
                share_to_org=share_to_org,
            )
            save_settings(updated)
            st.success("Settings saved.")
