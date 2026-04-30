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

# src/tools/chroma_manager.py
"""ChromaDB manager — per-user and shared-org document collections.

Each user gets an isolated collection named ``user_<id>_docs``.
Documents marked *shared* are also written to the org-wide
``CHROMA_SHARED_COLLECTION`` so they are searchable across users.

Scale note: for 10+ concurrent users replace PersistentClient with
``chromadb.HttpClient(host="...", port=8000)`` pointing at a ChromaDB
server process.
"""
import chromadb
from typing import List, Dict, Any, Optional

from src.config import CHROMA_DIR, CHROMA_SHARED_COLLECTION

_CHROMA_DIR: str = str(CHROMA_DIR)
_client: Optional[chromadb.ClientAPI] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client() -> chromadb.ClientAPI:
    """Return (and lazily initialise) the module-level ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=_CHROMA_DIR)
    return _client


def _user_collection_name(user_id: int) -> str:
    return f"user_{user_id}_docs"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_chunks(
    user_id: int,
    job_id: str,
    chunks: List[str],
    metadatas: List[Dict[str, Any]],
    embeddings: Optional[List[List[float]]] = None,
    shared: bool = False,
) -> None:
    """Persist text chunks (and optional pre-computed embeddings) to ChromaDB.

    Args:
        user_id:    Owner of the document.
        job_id:     Unique processing-job identifier used to generate chunk IDs.
        chunks:     Raw text strings to store.
        metadatas:  One metadata dict per chunk (must be same length as *chunks*).
        embeddings: Pre-computed embedding vectors (one per chunk).  When omitted
                    ChromaDB will compute them with its default model — useful for
                    quick local tests but slower and requires the ONNX model to be
                    cached.  In production this is always provided (nomic-embed-text
                    via embedding_manager.py).
        shared:     When True, also write to the shared org collection so other
                    users can discover this content via :func:`search_shared`.
    """
    client = _get_client()

    def _add(col_name: str) -> None:
        col = client.get_or_create_collection(col_name)
        ids = [f"{job_id}_{i}" for i in range(len(chunks))]
        enriched = [{**m, "job_id": job_id, "user_id": user_id} for m in metadatas]
        if embeddings is not None:
            col.add(documents=chunks, embeddings=embeddings, metadatas=enriched, ids=ids)
        else:
            col.add(documents=chunks, metadatas=enriched, ids=ids)

    _add(_user_collection_name(user_id))
    if shared:
        _add(CHROMA_SHARED_COLLECTION)


def delete_job_chunks(user_id: int, job_id: str) -> None:
    """Remove all chunks for *job_id* from the user's collection (and the
    shared collection, if present). Safe to call when collections / chunks
    don't exist."""
    client = _get_client()
    for col_name in (_user_collection_name(user_id), CHROMA_SHARED_COLLECTION):
        try:
            col = client.get_collection(col_name)
        except Exception:
            continue
        try:
            col.delete(where={"job_id": job_id})
        except Exception:
            # Older Chroma versions may raise on empty match; not fatal.
            pass


def delete_user_collection(user_id: int) -> None:
    """Drop the user's private collection entirely (e.g. for a "clear all" action).
    The shared collection is left untouched."""
    client = _get_client()
    try:
        client.delete_collection(_user_collection_name(user_id))
    except Exception:
        pass


def search_user(
    user_id: int,
    query_embedding: List[float],
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Search the private collection for *user_id*.

    Args:
        user_id:         Collection owner.
        query_embedding: Pre-computed query vector (must match the dimension used
                         when chunks were added).
        n_results:       Maximum number of results to return.

    Returns:
        List of dicts with keys ``content``, ``metadata``, and ``score``
        (1 − cosine distance, higher is better).
    """
    return _search(_user_collection_name(user_id), query_embedding, n_results)


def search_shared(
    query_embedding: List[float],
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Search the organisation-wide shared collection.

    Args:
        query_embedding: Pre-computed query vector.
        n_results:       Maximum number of results to return.

    Returns:
        List of dicts with keys ``content``, ``metadata``, and ``score``.
    """
    return _search(CHROMA_SHARED_COLLECTION, query_embedding, n_results)


# ---------------------------------------------------------------------------
# Internal search implementation
# ---------------------------------------------------------------------------

def _search(
    collection_name: str,
    query_embedding: List[float],
    n_results: int,
) -> List[Dict[str, Any]]:
    client = _get_client()
    try:
        col = client.get_collection(collection_name)
    except Exception:
        return []

    results = col.query(query_embeddings=[query_embedding], n_results=n_results)

    output: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"content": doc, "metadata": meta, "score": 1 - dist})
    return output
