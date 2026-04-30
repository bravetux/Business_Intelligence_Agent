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
import tempfile
from pathlib import Path
from datetime import datetime

@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Redirect DB_PATH to a temp file."""
    import src.tools.job_store as js
    monkeypatch.setattr(js, "DB_PATH", tmp_path / "test.db")
    js.init_schema()
    return tmp_path / "test.db"

def test_get_or_create_user(tmp_db):
    from src.tools.job_store import get_or_create_user
    user = get_or_create_user("alice")
    assert user.username == "alice"
    assert user.id > 0
    # idempotent
    user2 = get_or_create_user("alice")
    assert user2.id == user.id

def test_create_and_get_job(tmp_db):
    from src.tools.job_store import get_or_create_user, create_job, get_job
    from src.models.schemas import InputType, JobStatus
    user = get_or_create_user("bob")
    job = create_job(user.id, "meeting.mp3", InputType.AUDIO_VIDEO)
    assert job.status == JobStatus.QUEUED
    fetched = get_job(job.id)
    assert fetched.filename == "meeting.mp3"

def test_update_job_ready(tmp_db):
    from src.tools.job_store import get_or_create_user, create_job, update_job_status, get_job
    from src.models.schemas import InputType, JobStatus
    user = get_or_create_user("carol")
    job = create_job(user.id, "notes.txt", InputType.TRANSCRIPT)
    update_job_status(job.id, JobStatus.READY, normalised_text="Hello world")
    updated = get_job(job.id)
    assert updated.status == JobStatus.READY
    assert updated.normalised_text == "Hello world"

def test_settings_defaults(tmp_db):
    from src.tools.job_store import get_or_create_user, get_settings
    user = get_or_create_user("dave")
    settings = get_settings(user.id)
    assert settings.provider == "ollama"
    assert settings.share_to_org is False

def test_save_and_reload_settings(tmp_db):
    from src.tools.job_store import get_or_create_user, save_settings, get_settings
    from src.models.schemas import UserSettings
    user = get_or_create_user("eve")
    s = UserSettings(user_id=user.id, provider="bedrock", model="claude-3", target_lang="FR", share_to_org=True)
    save_settings(s)
    loaded = get_settings(user.id)
    assert loaded.provider == "bedrock"
    assert loaded.target_lang == "FR"
    assert loaded.share_to_org is True
