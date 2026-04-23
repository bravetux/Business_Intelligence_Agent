from strands import Agent
from src.models.schemas import AgentOutput

USER_STORY_SYSTEM_PROMPT = """You are an agile delivery specialist.
Convert the provided transcript or requirements into Jira-ready user stories.
For each distinct feature or requirement, produce:

## Story: [Story Title]
**As a** [user type]
**I want to** [action]
**So that** [benefit]

### Acceptance Criteria
- Given [context] When [action] Then [expected outcome]

### Subtasks
- [ ] [implementation subtask]

Be specific. Generate one story per distinct requirement. Do not invent requirements."""


def run_user_story_agent(text: str, model=None) -> AgentOutput:
    if model is None:
        from src.tools.provider_manager import get_model
        model = get_model()
    try:
        agent = Agent(model=model, system_prompt=USER_STORY_SYSTEM_PROMPT)
        response = agent(f"Generate user stories from the following content:\n\n{text}")
        return AgentOutput(agent_name="UserStoryAgent", content=str(response))
    except Exception as e:
        raise RuntimeError(f"UserStoryAgent failed: {e}") from e
