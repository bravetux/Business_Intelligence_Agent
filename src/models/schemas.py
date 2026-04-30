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

from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class InputType(str, Enum):
    AUDIO_VIDEO = "audio_video"
    TRANSCRIPT = "transcript"
    DOCUMENT = "document"


class User(BaseModel):
    id: int
    username: str
    created_at: datetime


class Job(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    user_id: int
    filename: str
    input_type: InputType
    status: JobStatus
    normalised_text: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: datetime


class UserSettings(BaseModel):
    user_id: int
    provider: str = "ollama"
    model: str = "llama3.3:70b"
    confluence_url: Optional[str] = None
    confluence_email: Optional[str] = None
    confluence_token: Optional[str] = None
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_token: Optional[str] = None
    target_lang: str = "EN"
    share_to_org: bool = False


class AgentOutput(BaseModel):
    agent_name: str
    content: str
    template_used: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = {}


class GenerationRequest(BaseModel):
    job_id: str
    user_id: int
    artefacts: List[str]          # ["mom", "kt_doc", "runbook", "user_story", "translation"]
    target_lang: Optional[str] = None
    push_confluence: bool = False
    push_jira: bool = False
    confluence_space: Optional[str] = None
    jira_project: Optional[str] = None
    provider: str = "ollama"
    model_id: str = "llama3.3:70b"
