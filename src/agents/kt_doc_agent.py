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
