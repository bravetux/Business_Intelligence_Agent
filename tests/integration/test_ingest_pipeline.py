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
import time
from pathlib import Path

@pytest.fixture
def patched_env(monkeypatch, tmp_path):
    """Patch DB, chroma, and embed so test runs without Ollama."""
    import src.tools.job_store as js
    import src.tools.chroma_manager as cm
    import src.tools.embedding_manager as em
    monkeypatch.setattr(js, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(cm, "_CHROMA_DIR", str(tmp_path / "chroma"))
    cm._client = None
    js.init_schema()
    monkeypatch.setattr(em, "embed_texts", lambda texts: [[0.1] * 768] * len(texts))
    return tmp_path

def test_text_transcript_ingest(patched_env):
    from src.tools.job_store import get_or_create_user, create_job, get_job
    from src.models.schemas import InputType, JobStatus
    from src.pipeline.ingest import start_ingest

    user = get_or_create_user("testuser")
    job = create_job(user.id, "notes.txt", InputType.TRANSCRIPT)

    txt_file = patched_env / "notes.txt"
    txt_file.write_text("Alice: we agreed to ship by Friday. Bob: I'll handle tests.")

    start_ingest(job_id=job.id, user_id=user.id,
                 file_path=txt_file, input_type=InputType.TRANSCRIPT, share_to_org=False)

    # poll up to 10 seconds
    for _ in range(20):
        j = get_job(job.id)
        if j.status in (JobStatus.READY, JobStatus.FAILED):
            break
        time.sleep(0.5)

    j = get_job(job.id)
    assert j.status == JobStatus.READY
    assert "Friday" in j.normalised_text
