import pytest
from unittest.mock import MagicMock
from src.models.schemas import AgentOutput

FIXTURE_TRANSCRIPT = """
Alice: Good morning everyone. Today we're deciding on the release date.
Bob: I think we should target next Friday, April 30th.
Alice: Agreed. Bob, you'll own the deployment checklist by Wednesday.
Carol: I'll handle comms to stakeholders by Thursday.
Alice: Any blockers? None raised. Great, meeting adjourned.
"""

def test_mom_agent_returns_agent_output(mocker):
    mock_model = MagicMock()
    mock_agent_response = MagicMock()
    mock_agent_response.__str__ = lambda self: (
        "## Decisions\nRelease date set to April 30th.\n"
        "## Action Items\n- Bob: deployment checklist by Wed\n- Carol: comms by Thu\n"
        "## Next Steps\nMonitor deployment."
    )
    mock_agent = MagicMock()
    mock_agent.return_value = mock_agent_response
    mocker.patch("src.agents.mom_agent.Agent", return_value=mock_agent)

    from src.agents.mom_agent import run_mom_agent
    result = run_mom_agent(FIXTURE_TRANSCRIPT, model=mock_model)

    assert isinstance(result, AgentOutput)
    assert result.agent_name == "MoMAgent"
    assert "Decisions" in result.content or len(result.content) > 10

def test_mom_agent_raises_on_llm_error(mocker):
    mock_model = MagicMock()
    mocker.patch("src.agents.mom_agent.Agent", side_effect=Exception("LLM error"))
    from src.agents.mom_agent import run_mom_agent
    with pytest.raises(RuntimeError, match="MoMAgent failed"):
        run_mom_agent("", model=mock_model)
