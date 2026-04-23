import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.config import DATA_DIR
from src.models.schemas import Job, JobStatus, InputType, User, UserSettings

DB_PATH = DATA_DIR / "jobs.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                input_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'QUEUED',
                normalised_text TEXT,
                error_msg TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL DEFAULT 'ollama',
                model TEXT NOT NULL DEFAULT 'llama3.3:70b',
                confluence_url TEXT,
                confluence_token TEXT,
                jira_url TEXT,
                jira_token TEXT,
                target_lang TEXT NOT NULL DEFAULT 'EN',
                share_to_org INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)


def get_or_create_user(username: str) -> User:
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not row:
            c.execute("INSERT INTO users (username, created_at) VALUES (?,?)", (username, now))
            row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    return User(id=row["id"], username=row["username"], created_at=datetime.fromisoformat(row["created_at"]))


def create_job(user_id: int, filename: str, input_type: InputType) -> Job:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO jobs (id,user_id,filename,input_type,status,created_at) VALUES (?,?,?,?,?,?)",
            (job_id, user_id, filename, input_type.value, JobStatus.QUEUED.value, now),
        )
    return Job(id=job_id, user_id=user_id, filename=filename, input_type=input_type,
               status=JobStatus.QUEUED, created_at=datetime.fromisoformat(now))


def update_job_status(job_id: str, status: JobStatus,
                      normalised_text: str = None, error_msg: str = None):
    with _conn() as c:
        if normalised_text is not None:
            c.execute("UPDATE jobs SET status=?, normalised_text=? WHERE id=?",
                      (status.value, normalised_text, job_id))
        elif error_msg is not None:
            c.execute("UPDATE jobs SET status=?, error_msg=? WHERE id=?",
                      (status.value, error_msg, job_id))
        else:
            c.execute("UPDATE jobs SET status=? WHERE id=?", (status.value, job_id))


def get_job(job_id: str) -> Optional[Job]:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    return Job(**{**d, "created_at": datetime.fromisoformat(d["created_at"])})


def list_jobs(user_id: int) -> List[Job]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM jobs WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    return [Job(**{**dict(r), "created_at": datetime.fromisoformat(r["created_at"])}) for r in rows]


def get_settings(user_id: int) -> UserSettings:
    with _conn() as c:
        row = c.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return UserSettings(user_id=user_id)
    d = dict(row)
    d["share_to_org"] = bool(d["share_to_org"])
    return UserSettings(**d)


def save_settings(s: UserSettings):
    with _conn() as c:
        c.execute("""
            INSERT INTO settings
              (user_id,provider,model,confluence_url,confluence_token,
               jira_url,jira_token,target_lang,share_to_org)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
              provider=excluded.provider, model=excluded.model,
              confluence_url=excluded.confluence_url,
              confluence_token=excluded.confluence_token,
              jira_url=excluded.jira_url, jira_token=excluded.jira_token,
              target_lang=excluded.target_lang, share_to_org=excluded.share_to_org
        """, (s.user_id, s.provider, s.model, s.confluence_url, s.confluence_token,
              s.jira_url, s.jira_token, s.target_lang, int(s.share_to_org)))
