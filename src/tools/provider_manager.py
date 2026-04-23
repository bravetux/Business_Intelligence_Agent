# src/tools/provider_manager.py
"""Provider configuration and model factory for Meeting & Document Intelligence Platform.

Supports: AWS Bedrock, Local Ollama, LM Studio, OpenRouter,
          Google Gemini, OpenAI / ChatGPT, Custom OpenAI-compatible endpoints.

Adapted from the 887-RAG sibling project provider_manager.py.

Priority: provider/model_id args > DEFAULT_PROVIDER/DEFAULT_MODEL from config.
"""
import logging
from typing import Optional

from src.config import (DEFAULT_PROVIDER, DEFAULT_MODEL, OLLAMA_HOST,
                        AWS_REGION, LMSTUDIO_HOST, OPENROUTER_API_KEY,
                        OPENAI_API_KEY, GEMINI_API_KEY)

logger = logging.getLogger(__name__)


def get_model(provider: str = None, model_id: str = None):
    """Return a Strands-compatible model object.

    Falls back to DEFAULT_PROVIDER / DEFAULT_MODEL from config if args are None.

    Supported providers: ollama, bedrock, lmstudio, openrouter, openai, gemini, custom

    Args:
        provider: Provider name (case-insensitive). Defaults to DEFAULT_PROVIDER.
        model_id: Model identifier string. Defaults to DEFAULT_MODEL.

    Returns:
        A Strands Model instance that can be passed to Agent(model=...).

    Raises:
        ValueError: If an unknown provider is specified.
        ImportError: If the provider's required package is not installed.
    """
    p = (provider or DEFAULT_PROVIDER).lower()
    m = model_id or DEFAULT_MODEL

    if p == "ollama":
        # Requires: uv add ollama
        from strands.models.ollama import OllamaModel
        return OllamaModel(host=OLLAMA_HOST, model_id=m)

    if p == "bedrock":
        from strands.models.bedrock import BedrockModel
        return BedrockModel(model_id=m, region_name=AWS_REGION)

    if p in ("lmstudio", "openai", "openrouter", "gemini", "custom"):
        from strands.models.openai import OpenAIModel

        base_urls = {
            "lmstudio": LMSTUDIO_HOST,
            "openrouter": "https://openrouter.ai/api/v1",
            "openai": "https://api.openai.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        }
        api_keys = {
            "lmstudio": "lm-studio",
            "openrouter": OPENROUTER_API_KEY,
            "openai": OPENAI_API_KEY,
            "gemini": GEMINI_API_KEY,
        }
        # OpenAIModel accepts client_args which are forwarded to openai.AsyncOpenAI()
        client_args = {
            "api_key": api_keys.get(p, ""),
            "base_url": base_urls.get(p, p),
        }
        return OpenAIModel(
            client_args=client_args,
            model_id=m,
        )

    raise ValueError(
        f"Unknown provider: '{p}'. "
        f"Supported: ollama, bedrock, lmstudio, openrouter, openai, gemini, custom"
    )
