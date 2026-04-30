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

import pytest
from pathlib import Path
from src.models.schemas import AgentOutput

@pytest.fixture
def sample_outputs():
    return {
        "mom": AgentOutput(agent_name="MoMAgent", content="# MoM\n- Decided: ship Friday"),
        "kt_doc": AgentOutput(agent_name="KTDocAgent", content="# KT Doc\n- Overview: login page"),
    }

def test_write_local_files(tmp_path, sample_outputs):
    from src.tools.output_writer import write_local
    written = write_local(job_id="job-123", outputs=sample_outputs, base_dir=tmp_path)
    assert (tmp_path / "job-123" / "mom.md").exists()
    assert (tmp_path / "job-123" / "kt_doc.md").exists()
    assert len(written) == 2

def test_push_confluence_error_is_caught(mocker, sample_outputs):
    mocker.patch("src.tools.output_writer.Confluence", side_effect=Exception("connection refused"))
    from src.tools.output_writer import push_confluence
    errors = push_confluence(
        outputs=sample_outputs, space_key="ENG",
        url="https://example.atlassian.net", token="fake"
    )
    assert len(errors) == 2  # both failed

def test_push_jira_error_is_caught(mocker):
    mocker.patch("src.tools.output_writer.Jira", side_effect=Exception("auth failed"))
    from src.tools.output_writer import push_jira
    story_output = AgentOutput(agent_name="UserStoryAgent", content="## Story: Login\nAs a user...")
    errors = push_jira(story_output=story_output, project_key="PROJ",
                       url="https://example.atlassian.net", token="fake")
    assert len(errors) == 1
