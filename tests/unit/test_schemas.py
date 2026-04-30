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
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models.schemas import (
    Job, JobStatus, InputType, User, UserSettings,
    AgentOutput, SearchResult, GenerationRequest
)

def test_job_status_values():
    assert JobStatus.QUEUED == "QUEUED"
    assert JobStatus.PROCESSING == "PROCESSING"
    assert JobStatus.READY == "READY"
    assert JobStatus.FAILED == "FAILED"

def test_job_model():
    job = Job(
        id="abc-123", user_id=1, filename="meeting.mp3",
        input_type=InputType.AUDIO_VIDEO, status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc)
    )
    assert job.normalised_text is None
    assert job.error_msg is None

def test_user_settings_defaults():
    s = UserSettings(user_id=1)
    assert s.provider == "ollama"
    assert s.model == "llama3.3:70b"
    assert s.share_to_org is False
    assert s.target_lang == "EN"

def test_generation_request_artefacts():
    req = GenerationRequest(
        job_id="abc", user_id=1, artefacts=["mom", "kt_doc"]
    )
    assert "mom" in req.artefacts
    assert req.push_confluence is False

def test_search_result():
    r = SearchResult(content="Some text", source="meeting.mp3", score=0.92)
    assert r.score == 0.92

def test_job_invalid_input_type():
    with pytest.raises(ValidationError):
        Job(
            id="x", user_id=1, filename="f.mp3",
            input_type="invalid_type", status="QUEUED",
            created_at=datetime.now(timezone.utc)
        )

def test_job_missing_required_fields():
    with pytest.raises(ValidationError):
        Job(id="x", user_id=1, filename="f.mp3", input_type="audio_video")
        # missing status and created_at

def test_generation_request_job_id_must_be_string():
    with pytest.raises(ValidationError):
        GenerationRequest(job_id=None, user_id=1, artefacts=["mom"])

def test_search_result_score_is_float():
    # verify score is stored as float
    r = SearchResult(content="text", source="file.txt", score="0.85")
    assert isinstance(r.score, float)
    assert r.score == 0.85
