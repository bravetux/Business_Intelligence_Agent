# src/agents/translation_agent.py
from pathlib import Path
from src.config import MODELS_DIR
from src.models.schemas import AgentOutput
from transformers import MarianTokenizer, MarianMTModel

SUPPORTED_PAIRS = {
    "EN-SV": "Helsinki-NLP/opus-mt-en-sv",
    "SV-EN": "Helsinki-NLP/opus-mt-sv-en",
    "EN-JP": "Helsinki-NLP/opus-mt-en-jap",
    "JP-EN": "Helsinki-NLP/opus-mt-jap-en",
    "EN-ZH": "Helsinki-NLP/opus-mt-en-zh",
    "ZH-EN": "Helsinki-NLP/opus-mt-zh-en",
    "EN-DE": "Helsinki-NLP/opus-mt-en-de",
    "DE-EN": "Helsinki-NLP/opus-mt-de-en",
    "EN-FR": "Helsinki-NLP/opus-mt-en-fr",
    "FR-EN": "Helsinki-NLP/opus-mt-fr-en",
}


def _local_path(pair_key: str) -> Path:
    model_id = SUPPORTED_PAIRS[pair_key]
    return MODELS_DIR / model_id.replace("/", "_")


def run_translation_agent(text: str, source_lang: str, target_lang: str) -> AgentOutput:
    """Translate text using a locally-downloaded Helsinki-NLP MarianMT model."""
    pair_key = f"{source_lang.upper()}-{target_lang.upper()}"
    if pair_key not in SUPPORTED_PAIRS:
        raise ValueError(f"Unsupported language pair: {pair_key}. Supported: {list(SUPPORTED_PAIRS)}")

    local = _local_path(pair_key)
    if not local.exists():
        raise RuntimeError(
            f"Model for {pair_key} not downloaded. "
            f"Run: python -m src.tools.setup_translation"
        )

    tokenizer = MarianTokenizer.from_pretrained(str(local))
    model = MarianMTModel.from_pretrained(str(local))

    inputs = tokenizer(text, return_tensors="pt", padding=True,
                       truncation=True, max_length=512)
    translated_ids = model.generate(**inputs)
    translated = tokenizer.decode(translated_ids[0], skip_special_tokens=True)

    return AgentOutput(
        agent_name="TranslationAgent",
        content=translated,
        metadata={"source_lang": source_lang, "target_lang": target_lang},
    )
