# app.py
import streamlit as st
import yaml
from pathlib import Path

st.set_page_config(page_title="P04 — Meeting Intelligence", layout="wide")

AUTH_YAML = Path(__file__).parent / "auth.yaml"

if not AUTH_YAML.exists():
    st.error("auth.yaml not found. Run: `uv run python -m src.tools.init_db` first.")
    st.stop()

import streamlit_authenticator as stauth

with open(AUTH_YAML) as f:
    auth_cfg = yaml.safe_load(f)

authenticator = stauth.Authenticate(
    auth_cfg["credentials"],
    auth_cfg["cookie"]["name"],
    auth_cfg["cookie"]["key"],
    auth_cfg["cookie"]["expiry_days"],
)

# v0.3.x: login() renders the form and sets st.session_state keys.
# It returns None when location is 'main' or 'sidebar'.
authenticator.login(location="main")

auth_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

if auth_status is False:
    st.error("Username or password is incorrect.")
    st.stop()

if auth_status is None:
    st.info("Please enter your username and password.")
    st.stop()

from src.tools.job_store import get_or_create_user, init_schema
init_schema()
user = get_or_create_user(username)
st.session_state["user_id"] = user.id
st.session_state["username"] = username

authenticator.logout(button_name="Logout", location="sidebar")
st.sidebar.write(f"Logged in as **{name}**")

tab_upload, tab_generate, tab_search, tab_history, tab_settings = st.tabs([
    "Upload & Ingest", "Generate Artefacts", "Search", "History", "Settings"
])

from src.ui import upload_tab, generate_tab, search_tab, history_tab, settings_tab

with tab_upload:
    upload_tab.render(user.id)

with tab_generate:
    generate_tab.render(user.id)

with tab_search:
    search_tab.render(user.id)

with tab_history:
    history_tab.render(user.id)

with tab_settings:
    settings_tab.render(user.id)
