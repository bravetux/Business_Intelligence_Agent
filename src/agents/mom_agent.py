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
