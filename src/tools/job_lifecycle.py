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

# src/tools/job_lifecycle.py
"""Cross-store delete helpers for jobs.

Cleanly removes a job from every place it lives:
  - SQLite row (jobs table)
  - ChromaDB chunks (per-user + shared collections)
  - Local artefact directory under data/jobs/{job_id}/

Uploaded source files in data/uploads/ are intentionally left in place — multiple
jobs may reference the same uploaded filename, and deleting it could break
sibling jobs.
"""
import logging
import shutil
from typing import List

from src.config import JOBS_DIR
from src.tools import job_store, chroma_manager

logger = logging.getLogger(__name__)


def delete_job(job_id: str, user_id: int) -> bool:
    """Remove one job and all of its derived state. Returns True on success."""
    removed = job_store.delete_job(job_id, user_id)
    if not removed:
        return False
    try:
        chroma_manager.delete_job_chunks(user_id, job_id)
    except Exception:
        logger.exception("Failed to delete chroma chunks for job %s", job_id)
    job_dir = JOBS_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
    return True


def delete_all_jobs(user_id: int) -> int:
    """Remove every job belonging to user_id. Returns the count removed."""
    job_ids: List[str] = job_store.delete_all_jobs(user_id)
    for jid in job_ids:
        job_dir = JOBS_DIR / jid
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
    # Drop the entire user collection in one shot — faster than per-job deletes.
    try:
        chroma_manager.delete_user_collection(user_id)
    except Exception:
        logger.exception("Failed to drop chroma collection for user %s", user_id)
    return len(job_ids)
