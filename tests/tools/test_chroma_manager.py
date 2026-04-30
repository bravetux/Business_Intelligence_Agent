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

# tests/tools/test_chroma_manager.py
"""
Tests for chroma_manager — per-user and shared-org collections.

Explicit 768-dim embeddings are passed in every add_chunks call so that:
  1. Tests are fast (no network download of ChromaDB's default ONNX model).
  2. Dimensions match production usage (nomic-embed-text → 768 dims).
  3. search_user / search_shared can use query_embeddings of the same size.
"""
import pytest

_DIM = 768  # nomic-embed-text output dimension (matches production)
_EMB_A = [[0.1] * _DIM]   # fake embedding for user-1 chunk
_EMB_B = [[0.2] * _DIM]   # fake embedding for user-2 chunk
_QUERY = [0.1] * _DIM     # query vector (same dim)


@pytest.fixture
def chroma_tmp(monkeypatch, tmp_path):
    import src.tools.chroma_manager as cm
    monkeypatch.setattr(cm, "_CHROMA_DIR", str(tmp_path / "chroma"))
    cm._client = None  # force re-init with the temp directory
    yield cm


def test_user_collection_isolated(chroma_tmp):
    """Chunks added for user_1 must not appear in user_2's search results."""
    cm = chroma_tmp
    cm.add_chunks(
        user_id=1,
        job_id="job-a",
        chunks=["Hello world"],
        metadatas=[{"source": "a.txt"}],
        embeddings=_EMB_A,
    )
    cm.add_chunks(
        user_id=2,
        job_id="job-b",
        chunks=["Goodbye world"],
        metadatas=[{"source": "b.txt"}],
        embeddings=_EMB_B,
    )
    results = cm.search_user(user_id=1, query_embedding=_QUERY, n_results=5)
    sources = [r["metadata"]["source"] for r in results]
    assert "a.txt" in sources
    assert "b.txt" not in sources


def test_shared_collection(chroma_tmp):
    """A chunk added with shared=True must appear in search_shared results."""
    cm = chroma_tmp
    cm.add_chunks(
        user_id=1,
        job_id="job-a",
        chunks=["Shared content"],
        metadatas=[{"source": "s.txt"}],
        embeddings=_EMB_A,
        shared=True,
    )
    results = cm.search_shared(query_embedding=_QUERY, n_results=5)
    sources = [r["metadata"]["source"] for r in results]
    assert "s.txt" in sources
