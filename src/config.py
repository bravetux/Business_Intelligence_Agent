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
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "http://localhost:1234/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_CHUNK_SIZE = int(os.getenv("EMBED_CHUNK_SIZE", "512"))
EMBED_CHUNK_OVERLAP = int(os.getenv("EMBED_CHUNK_OVERLAP", "50"))

CHROMA_SHARED_COLLECTION = "org_shared_docs"

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")
JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")
