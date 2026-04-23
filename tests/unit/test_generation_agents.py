import pytest
from unittest.mock import MagicMock
from src.models.schemas import AgentOutput

FIXTURE_TEXT = "We need a login page with username and password fields. It should validate email format."

def _make_mock_agent(mocker, module_path: str, response_text: str):
    mock_resp = MagicMock()
    mock_resp.__str__ = lambda self: response_text
    mock_ag = MagicMock(return_value=mock_resp)
    mocker.patch(f"{module_path}.Agent", return_value=mock_ag)
    return MagicMock()  # mock model

def test_kt_doc_agent(mocker):
    model = _make_mock_agent(mocker, "src.agents.kt_doc_agent", "## Overview\nLogin page docs.")
    from src.agents.kt_doc_agent import run_kt_doc_agent
    result = run_kt_doc_agent(FIXTURE_TEXT, model=model)
    assert isinstance(result, AgentOutput)
    assert result.agent_name == "KTDocAgent"

def test_runbook_agent(mocker):
    model = _make_mock_agent(mocker, "src.agents.runbook_updater", "## Problem\nLogin fails.")
    from src.agents.runbook_updater import run_runbook_agent
    result = run_runbook_agent(FIXTURE_TEXT, model=model)
    assert isinstance(result, AgentOutput)
    assert result.agent_name == "RunbookUpdater"

def test_user_story_agent(mocker):
    model = _make_mock_agent(mocker, "src.agents.user_story_agent", "## Story: Login\nAs a user...")
    from src.agents.user_story_agent import run_user_story_agent
    result = run_user_story_agent(FIXTURE_TEXT, model=model)
    assert isinstance(result, AgentOutput)
    assert result.agent_name == "UserStoryAgent"
