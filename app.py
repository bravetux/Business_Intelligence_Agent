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

# app.py
import streamlit as st
import yaml
from pathlib import Path

st.set_page_config(page_title="Meeting Intelligence", layout="wide")

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

from src.ui import landing


def _render_unauthenticated_landing(auth_status):
    """Hero + login form + full feature catalogue."""
    landing.render_hero()

    # Center the login form in a narrower middle column for visual balance.
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; font-weight:600; color:#1F4E79; "
                "font-size:1.1rem; margin-bottom:0.4rem;'>Sign in to continue</div>",
                unsafe_allow_html=True,
            )
            authenticator.login(location="main")
            if auth_status is False:
                st.error("Username or password is incorrect.")
            elif auth_status is None:
                st.caption(
                    "Default credentials after a fresh install: "
                    "**admin** / **changeme**. "
                    "Change the password in Settings after first login."
                )

    landing.render_features()


# ── First pass: read current auth state ────────────────────────────────────
auth_status = st.session_state.get("authentication_status")

if auth_status is not True:
    _render_unauthenticated_landing(auth_status)
    st.stop()

# ── Authenticated — proceed to the app ─────────────────────────────────────
name = st.session_state.get("name")
username = st.session_state.get("username")

from src.tools.job_store import get_or_create_user, init_schema
init_schema()
user = get_or_create_user(username)
st.session_state["user_id"] = user.id
st.session_state["username"] = username

authenticator.logout(button_name="Logout", location="sidebar")
st.sidebar.write(f"Logged in as **{name}**")

tab_home, tab_upload, tab_generate, tab_search, tab_history, tab_settings = st.tabs([
    "Home", "Upload & Ingest", "Generate Artefacts", "Search", "History", "Settings"
])

from src.ui import home_tab, upload_tab, generate_tab, search_tab, history_tab, settings_tab

with tab_home:
    home_tab.render(name)

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
