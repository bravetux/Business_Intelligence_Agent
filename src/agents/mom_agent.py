# src/agents/mom_agent.py
from strands import Agent
from src.models.schemas import AgentOutput

MOM_SYSTEM_PROMPT = """You are a Meeting Intelligence assistant specialising in Minutes of Meeting.
Given a meeting transcript, extract and structure:
1. Meeting title and date (if mentioned)
2. Attendees (if mentioned)
3. Key decisions made (be specific)
4. Action items — each with owner name and due date if mentioned
5. Next steps
6. Open questions or blockers

Output as clean markdown with clear section headings.
Be concise. Do not invent information not present in the transcript."""


def run_mom_agent(transcript: str, model=None) -> AgentOutput:
    """Extract Minutes of Meeting from a transcript."""
    if model is None:
        from src.tools.provider_manager import get_model
        model = get_model()
    try:
        agent = Agent(model=model, system_prompt=MOM_SYSTEM_PROMPT)
        response = agent(
            f"Extract the minutes of meeting from this transcript:\n\n{transcript}"
        )
        return AgentOutput(agent_name="MoMAgent", content=str(response))
    except Exception as e:
        raise RuntimeError(f"MoMAgent failed: {e}") from e
