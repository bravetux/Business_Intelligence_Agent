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

import pytest
from unittest.mock import MagicMock
from src.models.schemas import SearchResult


def test_search_returns_results(mocker):
    mocker.patch("src.agents.doc_search_agent.embedding_manager.embed_query",
                 return_value=[0.1] * 768)
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_user",
                 return_value=[{"content": "Alice agreed to ship Friday.", "metadata": {"source": "meeting.txt"}, "score": 0.9}])
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_shared", return_value=[])

    mock_resp = MagicMock()
    mock_resp.__str__ = lambda self: "Alice agreed to ship on Friday."
    mock_agent = MagicMock(return_value=mock_resp)
    mocker.patch("src.agents.doc_search_agent.Agent", return_value=mock_agent)

    from src.agents.doc_search_agent import run_doc_search
    answer, sources = run_doc_search(
        query="When will they ship?",
        user_id=1,
        include_shared=False,
        model=MagicMock(),
    )
    assert "Friday" in answer
    assert len(sources) == 1
    assert sources[0].source == "meeting.txt"


def test_search_includes_shared_when_opted_in(mocker):
    mocker.patch("src.agents.doc_search_agent.embedding_manager.embed_query",
                 return_value=[0.1] * 768)
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_user", return_value=[])
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_shared",
                 return_value=[{"content": "Org-wide policy update.", "metadata": {"source": "policy.pdf"}, "score": 0.85}])
    mock_resp = MagicMock()
    mock_resp.__str__ = lambda self: "Policy update content."
    mocker.patch("src.agents.doc_search_agent.Agent", return_value=MagicMock(return_value=mock_resp))

    from src.agents.doc_search_agent import run_doc_search
    answer, sources = run_doc_search("policy update", user_id=1, include_shared=True, model=MagicMock())
    assert any(s.source == "policy.pdf" for s in sources)


def test_search_returns_no_docs_message(mocker):
    mocker.patch("src.agents.doc_search_agent.embedding_manager.embed_query", return_value=[0.1]*768)
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_user", return_value=[])
    mocker.patch("src.agents.doc_search_agent.chroma_manager.search_shared", return_value=[])

    from src.agents.doc_search_agent import run_doc_search
    answer, sources = run_doc_search("anything", user_id=1, include_shared=False, model=MagicMock())
    assert "No relevant documents" in answer
    assert sources == []
