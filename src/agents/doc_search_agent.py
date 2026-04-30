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

# src/agents/doc_search_agent.py
from typing import List, Tuple
from strands import Agent
from src.tools import embedding_manager, chroma_manager
from src.models.schemas import SearchResult

DOC_SEARCH_SYSTEM_PROMPT = """You are a document search assistant.
You will be given a user question and relevant document excerpts with their sources.
Synthesise a clear, accurate answer based ONLY on the provided excerpts.
After your answer, list the sources you used.
If the excerpts do not contain enough information, say so clearly — do not guess."""


def run_doc_search(query: str, user_id: int,
                   include_shared: bool = False,
                   n_results: int = 5,
                   model=None,
                   llm_provider: str = "ollama") -> Tuple[str, List[SearchResult]]:
    """
    Returns (synthesised_answer, list_of_SearchResult).
    include_shared=True queries org_shared_docs in addition to the user's private collection.
    llm_provider selects the embedding backend (must match what was used at ingest).
    """
    if model is None:
        from src.tools.provider_manager import get_model
        model = get_model()

    embed_provider = embedding_manager.resolve_embed_provider(llm_provider)
    query_embedding = embedding_manager.embed_query(query, provider=embed_provider)

    raw_results = chroma_manager.search_user(user_id, query_embedding, n_results)
    if include_shared:
        shared = chroma_manager.search_shared(query_embedding, n_results)
        raw_results = _deduplicate(raw_results + shared)

    if not raw_results:
        return "No relevant documents found.", []

    context = "\n\n".join(
        f"[Source: {r['metadata']['source']}]\n{r['content']}"
        for r in raw_results
    )
    agent = Agent(model=model, system_prompt=DOC_SEARCH_SYSTEM_PROMPT)
    response = agent(f"Question: {query}\n\nDocument excerpts:\n{context}")

    sources = [
        SearchResult(
            content=r["content"],
            source=r["metadata"].get("source", "unknown"),
            score=r["score"],
            metadata=r["metadata"],
        )
        for r in raw_results
    ]
    return str(response), sources


def _deduplicate(results: list) -> list:
    seen = set()
    out = []
    for r in results:
        key = r["content"][:100]
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
