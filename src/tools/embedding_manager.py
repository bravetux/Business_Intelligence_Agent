# src/tools/embedding_manager.py
"""Embedding utilities using Ollama's embedding API.

Uses nomic-embed-text (or the model set in EMBED_MODEL) via the Ollama
/api/embeddings endpoint. No additional packages required beyond requests.
"""
import requests
from typing import List

from src.config import OLLAMA_HOST, EMBED_MODEL


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of strings using the configured embed model via Ollama.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (one per input string).

    Raises:
        requests.HTTPError: If the Ollama API returns an error response.
        requests.Timeout: If the request times out after 60 seconds.
    """
    embeddings = []
    for text in texts:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"])
    return embeddings


def embed_query(text: str) -> List[float]:
    """Embed a single query string.

    Args:
        text: The query string to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    return embed_texts([text])[0]
