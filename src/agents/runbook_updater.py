from strands import Agent
from src.models.schemas import AgentOutput

RUNBOOK_SYSTEM_PROMPT = """You are a runbook maintenance specialist.
Given meeting notes or incident discussions, produce a structured runbook section in markdown:
1. Problem Statement
2. Detection Criteria
3. Investigation Steps (numbered)
4. Resolution Steps (numbered)
5. Escalation Path
6. Post-Incident Actions

Mark new content with [NEW] and updated procedures with [UPDATED].
Do not invent information not present in the input."""


def run_runbook_agent(text: str, model=None) -> AgentOutput:
    if model is None:
        from src.tools.provider_manager import get_model
        model = get_model()
    try:
        agent = Agent(model=model, system_prompt=RUNBOOK_SYSTEM_PROMPT)
        response = agent(f"Create or update a runbook section from the following notes:\n\n{text}")
        return AgentOutput(agent_name="RunbookUpdater", content=str(response))
    except Exception as e:
        raise RuntimeError(f"RunbookUpdater failed: {e}") from e
