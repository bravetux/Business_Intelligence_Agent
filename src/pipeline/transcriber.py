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
