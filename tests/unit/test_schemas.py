import pytest
from datetime import datetime
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
        created_at=datetime.utcnow()
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
