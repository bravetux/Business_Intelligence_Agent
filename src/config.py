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

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
JOBS_DIR = DATA_DIR / "jobs"
CHROMA_DIR = DATA_DIR / "chroma"
MODELS_DIR = DATA_DIR / "models"
TEMPLATES_DIR = BASE_DIR / "templates"
AUTH_YAML_PATH = BASE_DIR / "auth.yaml"

for _d in [DATA_DIR, UPLOADS_DIR, JOBS_DIR, CHROMA_DIR, MODELS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "ollama")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.3:70b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "http://localhost:1234/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.1"))
AGENT_TOP_P = float(os.getenv("AGENT_TOP_P", "0.9"))
AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "32768"))

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
EMBED_CHUNK_SIZE = int(os.getenv("EMBED_CHUNK_SIZE", "512"))
EMBED_CHUNK_OVERLAP = int(os.getenv("EMBED_CHUNK_OVERLAP", "50"))

CHROMA_SHARED_COLLECTION = "org_shared_docs"

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")
JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")
