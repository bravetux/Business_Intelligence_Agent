from pathlib import Path
from typing import Dict, Any
from src.config import WHISPER_MODEL_SIZE


def transcribe(audio_path: Path) -> Dict[str, Any]:
    """
    Transcribe audio/video file using faster-whisper.
    Returns dict with keys: language, duration, segments, full_text.

    Scale note: For concurrent transcription jobs, move this call into a
    Celery task so multiple whisper models don't load simultaneously.
    """
    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(str(audio_path), beam_size=5)

    segments = []
    for seg in segments_iter:
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })

    full_text = " ".join(s["text"] for s in segments)
    return {
        "language": info.language,
        "duration": round(info.duration, 2),
        "segments": segments,
        "full_text": full_text,
    }
