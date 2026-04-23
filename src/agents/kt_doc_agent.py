from strands import Agent
from src.models.schemas import AgentOutput

KT_DOC_SYSTEM_PROMPT = """You are a Knowledge Transfer documentation specialist.
Convert the provided transcript or notes into a structured KT document with sections:
1. Overview / Purpose
2. System / Process Description
3. Key Components
4. Step-by-Step Procedures
5. Known Issues / Gotchas
6. References

Use clear markdown headings. Be comprehensive but concise. Do not invent information."""


def run_kt_doc_agent(text: str, model=None) -> AgentOutput:
    if model is None:
        from src.tools.provider_manager import get_model
        model = get_model()
    try:
        agent = Agent(model=model, system_prompt=KT_DOC_SYSTEM_PROMPT)
        response = agent(f"Create a KT document from the following content:\n\n{text}")
        return AgentOutput(agent_name="KTDocAgent", content=str(response))
    except Exception as e:
        raise RuntimeError(f"KTDocAgent failed: {e}") from e
