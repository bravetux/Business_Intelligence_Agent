# src/agents/orchestrator.py
"""
Python dispatcher orchestrator — routes GenerationRequest to the correct sub-agents.
Each sub-agent is a Strands Agent internally; routing logic is deterministic Python (not LLM).

Scale note: This runs synchronously per request. For 10+ concurrent users add a Celery
task wrapper here so generation jobs queue rather than blocking the Streamlit thread.
"""
from typing import Dict
from src.models.schemas import AgentOutput, GenerationRequest


def run_orchestrator(request: GenerationRequest,
                     normalised_text: str,
                     model=None) -> Dict[str, AgentOutput]:
    """
    Dispatches to sub-agents based on request.artefacts.
    Returns dict keyed by artefact name e.g. {"mom": AgentOutput, "kt_doc": AgentOutput}.
    Translation runs last and adds translated variants: {"mom_translated_FR": AgentOutput}.
    """
    from src.tools.provider_manager import get_model as _get_model
    m = model or _get_model(request.provider, request.model_id)

    results: Dict[str, AgentOutput] = {}

    if "mom" in request.artefacts:
        from src.agents.mom_agent import run_mom_agent
        results["mom"] = run_mom_agent(normalised_text, model=m)

    if "kt_doc" in request.artefacts:
        from src.agents.kt_doc_agent import run_kt_doc_agent
        results["kt_doc"] = run_kt_doc_agent(normalised_text, model=m)

    if "runbook" in request.artefacts:
        from src.agents.runbook_updater import run_runbook_agent
        results["runbook"] = run_runbook_agent(normalised_text, model=m)

    if "user_story" in request.artefacts:
        from src.agents.user_story_agent import run_user_story_agent
        results["user_story"] = run_user_story_agent(normalised_text, model=m)

    if "translation" in request.artefacts and request.target_lang:
        from src.agents.translation_agent import run_translation_agent
        lang = request.target_lang.upper()
        for key in list(results.keys()):
            try:
                translated = run_translation_agent(results[key].content,
                                                   source_lang="EN",
                                                   target_lang=lang)
                results[f"{key}_translated_{lang}"] = translated
            except RuntimeError:
                results[f"{key}_translated_{lang}"] = AgentOutput(
                    agent_name="TranslationAgent",
                    content=f"[Translation unavailable — model for EN-{lang} not downloaded]",
                )

    return results
