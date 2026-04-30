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

# src/ui/home_tab.py
"""Post-login home tab — hero + same feature catalogue shown on the login page,
plus a personalised welcome line and a quick-start nudge."""
import streamlit as st

from src.ui import landing


def render(username: str):
    landing.render_hero()
    st.markdown(
        f"<div style='text-align:center; font-size:1.05rem; margin-bottom:0.6rem;'>"
        f"Welcome, <b>{username}</b>.</div>",
        unsafe_allow_html=True,
    )
    landing.render_features()
