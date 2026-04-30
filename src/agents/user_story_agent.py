# Business Intelligence Agent
# Copyright (C) 2026  B. Vignesh Kumar (Bravetux) <ic19939@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
