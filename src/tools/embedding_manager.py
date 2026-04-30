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

# src/tools/embedding_manager.py
"""Embedding utilities — supports Ollama (local) and AWS Bedrock Titan.

Provider routing is keyed on the user's configured LLM provider:
  - "aws" / "bedrock"  -> Bedrock Titan (BEDROCK_EMBED_MODEL)
  - everything else    -> Ollama (EMBED_MODEL)

Tests can still monkeypatch embed_texts / embed_query — the *args/**kwargs
shape preserves the legacy positional-only call signature.
"""
import json
import logging
from typing import List, Optional

import requests

from src.config import (
    OLLAMA_HOST,
    EMBED_MODEL,
    BEDROCK_EMBED_MODEL,
    AWS_REGION,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_texts(
    texts: List[str],
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    region: Optional[str] = None,
) -> List[List[float]]:
    """Embed a list of strings.

    Args:
        texts:    Strings to embed.
        provider: "ollama" (default), "aws"/"bedrock". None falls back to ollama.
        model:    Model id; defaults to EMBED_MODEL or BEDROCK_EMBED_MODEL.
        region:   AWS region for Bedrock; defaults to AWS_REGION.
    """
    p = (provider or "ollama").lower()
    if p in ("aws", "bedrock"):
        return _embed_bedrock(texts, model or BEDROCK_EMBED_MODEL, region or AWS_REGION)
    return _embed_ollama(texts, model or EMBED_MODEL)


def embed_query(
    text: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    region: Optional[str] = None,
) -> List[float]:
    """Embed a single query string. See :func:`embed_texts`."""
    return embed_texts([text], provider=provider, model=model, region=region)[0]


def resolve_embed_provider(llm_provider: str) -> str:
    """Map a chat-LLM provider name to the matching embed provider."""
    if (llm_provider or "").lower() in ("aws", "bedrock"):
        return "aws"
    return "ollama"


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def _embed_ollama(texts: List[str], model: str) -> List[List[float]]:
    embeddings = []
    for text in texts:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"])
    return embeddings


def _embed_bedrock(texts: List[str], model: str, region: str) -> List[List[float]]:
    # boto3 reads AWS_ACCESS_KEY_ID/SECRET/SESSION_TOKEN from env after load_dotenv().
    import boto3

    client = boto3.client("bedrock-runtime", region_name=region)
    embeddings = []
    for text in texts:
        body = json.dumps({"inputText": text})
        resp = client.invoke_model(
            modelId=model,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        payload = json.loads(resp["body"].read())
        embeddings.append(payload["embedding"])
    return embeddings
