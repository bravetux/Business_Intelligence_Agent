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
