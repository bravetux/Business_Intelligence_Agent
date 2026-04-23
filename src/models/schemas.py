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
    confluence_token: Optional[str] = None
    jira_url: Optional[str] = None
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
