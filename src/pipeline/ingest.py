# src/pipeline/ingest.py
import threading
import logging
from pathlib import Path
from src.models.schemas import InputType, JobStatus
from src.tools import job_store, chroma_manager, embedding_manager
from src.config import EMBED_CHUNK_SIZE, EMBED_CHUNK_OVERLAP

logger = logging.getLogger(__name__)

# Scale note: Replace threading.Thread with a Celery task for 10+ concurrent users.
# Signature stays the same — just decorate start_ingest with @celery_app.task.


def start_ingest(job_id: str, user_id: int, file_path: Path,
                 input_type: InputType, share_to_org: bool = False):
    """Launch ingestion in a background thread. Returns immediately."""
    t = threading.Thread(
        target=_run_ingest,
        args=(job_id, user_id, file_path, input_type, share_to_org),
        daemon=True,
    )
    t.start()


def _run_ingest(job_id: str, user_id: int, file_path: Path,
                input_type: InputType, share_to_org: bool):
    job_store.update_job_status(job_id, JobStatus.PROCESSING)
    try:
        text = _extract_text(file_path, input_type)
        chunks, metadatas = _chunk(text, str(file_path.name))
        embeddings = embedding_manager.embed_texts(chunks)
        chroma_manager.add_chunks(
            user_id=user_id, job_id=job_id,
            chunks=chunks, metadatas=metadatas,
            embeddings=embeddings,          # pass pre-computed nomic-embed-text vectors
            shared=share_to_org,
        )
        job_store.update_job_status(job_id, JobStatus.READY, normalised_text=text)
    except Exception as e:
        logger.exception("Ingest failed for job %s", job_id)
        job_store.update_job_status(job_id, JobStatus.FAILED, error_msg=str(e))


def _extract_text(file_path: Path, input_type: InputType) -> str:
    if input_type == InputType.TRANSCRIPT:
        return file_path.read_text(encoding="utf-8")
    if input_type == InputType.AUDIO_VIDEO:
        from src.pipeline.transcriber import transcribe
        result = transcribe(file_path)
        return result["full_text"]
    if input_type == InputType.DOCUMENT:
        from src.pipeline.doc_parser import parse_document
        return parse_document(file_path)
    raise ValueError(f"Unknown input_type: {input_type}")


def _chunk(text: str, source: str):
    size = EMBED_CHUNK_SIZE
    overlap = EMBED_CHUNK_OVERLAP
    words = text.split()
    chunks, metadatas = [], []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + size])
        chunks.append(chunk)
        metadatas.append({"source": source, "chunk_index": len(chunks) - 1})
        i += size - overlap
    return chunks, metadatas
