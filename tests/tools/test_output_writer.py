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
