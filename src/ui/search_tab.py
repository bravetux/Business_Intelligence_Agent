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

# src/ui/search_tab.py
import streamlit as st
from src.tools.job_store import get_settings
from src.agents.doc_search_agent import run_doc_search


def render(user_id: int):
    st.header("Document Search")
    settings = get_settings(user_id)
    query = st.text_input("Your question", placeholder="What was decided about the release date?")
    include_shared = st.checkbox("Include shared org library", value=settings.share_to_org)
    n_results = st.slider("Max source chunks", 3, 10, 5)

    if st.button("Search", disabled=not query.strip()):
        with st.spinner("Searching…"):
            try:
                answer, sources = run_doc_search(
                    query=query, user_id=user_id,
                    include_shared=include_shared, n_results=n_results,
                    llm_provider=settings.provider,
                )
                st.markdown("### Answer")
                st.markdown(answer)
                if sources:
                    st.markdown("### Sources")
                    for s in sources:
                        with st.expander(f"{s.source}  (score: {s.score:.2f})"):
                            st.write(s.content)
            except Exception as e:
                st.error(f"Search failed: {e}")
