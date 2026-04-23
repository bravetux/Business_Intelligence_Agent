# tests/unit/test_orchestrator.py
"""
Unit tests for the orchestrator dispatcher.

Mocking approach: sub-agent functions are imported INSIDE run_orchestrator's function body
(lazy imports to avoid circular dependencies). Because the names are never bound at module
level in orchestrator.py, patching 'src.agents.orchestrator.run_mom_agent' would fail.
Instead we patch at the SOURCE module (e.g. 'src.agents.mom_agent.run_mom_agent'), which
is where the name lives when Python resolves 'from src.agents.mom_agent import run_mom_agent'
at call time.

We always pass model=mock_model so the 'model or _get_model(...)' branch never calls
src.tools.provider_manager.get_model — no provider credentials needed.
"""
import pytest
from unittest.mock import MagicMock
from src.models.schemas import GenerationRequest, AgentOutput


@pytest.fixture
def mock_model():
    return MagicMock()


def test_orchestrator_dispatches_mom_only(mocker, mock_model):
    """Only 'mom' in artefacts → only MoM agent runs; kt_doc not called."""
    mock_output = AgentOutput(agent_name="MoMAgent", content="Meeting summary")
    mock_run_mom = mocker.patch("src.agents.mom_agent.run_mom_agent",
                                return_value=mock_output)
    mock_run_kt = mocker.patch("src.agents.kt_doc_agent.run_kt_doc_agent")

    from src.agents.orchestrator import run_orchestrator
    req = GenerationRequest(job_id="j1", user_id=1, artefacts=["mom"])
    results = run_orchestrator(req, "transcript text", model=mock_model)

    assert "mom" in results
    assert results["mom"].content == "Meeting summary"
    assert "kt_doc" not in results
    mock_run_mom.assert_called_once()
    mock_run_kt.assert_not_called()


def test_orchestrator_dispatches_multiple(mocker, mock_model):
    """Both 'mom' and 'kt_doc' in artefacts → both agents run."""
    mocker.patch("src.agents.mom_agent.run_mom_agent",
                 return_value=AgentOutput(agent_name="MoMAgent", content="MoM content"))
    mocker.patch("src.agents.kt_doc_agent.run_kt_doc_agent",
                 return_value=AgentOutput(agent_name="KTDocAgent", content="KT content"))

    from src.agents.orchestrator import run_orchestrator
    req = GenerationRequest(job_id="j2", user_id=1, artefacts=["mom", "kt_doc"])
    results = run_orchestrator(req, "some text", model=mock_model)

    assert "mom" in results and "kt_doc" in results
    assert results["mom"].content == "MoM content"
    assert results["kt_doc"].content == "KT content"


def test_orchestrator_translation_unavailable(mocker, mock_model):
    """When translation model not downloaded, result contains 'unavailable' message."""
    mocker.patch("src.agents.mom_agent.run_mom_agent",
                 return_value=AgentOutput(agent_name="MoMAgent", content="MoM content"))
    mocker.patch("src.agents.translation_agent.run_translation_agent",
                 side_effect=RuntimeError("not downloaded"))

    from src.agents.orchestrator import run_orchestrator
    req = GenerationRequest(job_id="j3", user_id=1, artefacts=["mom", "translation"],
                            target_lang="JP")
    results = run_orchestrator(req, "text", model=mock_model)

    assert "mom_translated_JP" in results
    assert "unavailable" in results["mom_translated_JP"].content
