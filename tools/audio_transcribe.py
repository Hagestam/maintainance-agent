# tools/audio_transcribe.py
"""
Transcribe WhatsApp voice notes (usually OGG/Opus) with local Whisper.

No OpenAI API key — Claude still handles the agent; this only turns speech into text.
Requires: pip install faster-whisper, and system ffmpeg for OGG/Opus.
"""
from __future__ import annotations

import base64
import logging
import tempfile
from functools import lru_cache

logger = logging.getLogger(__name__)

_EXT_BY_MIME = {
    "audio/ogg": ".ogg",
    "audio/opus": ".ogg",
    "application/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".mp4",
    "audio/m4a": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/amr": ".amr",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
}

# "tiny" / "base" are fast enough for short WhatsApp voice notes.
_WHISPER_MODEL_SIZE = "base"


def _normalize_mime(mime_type: str) -> str:
    return (mime_type or "").lower().split(";")[0].strip()


@lru_cache(maxsize=1)
def _get_whisper_model():
    from faster_whisper import WhisperModel

    # CPU + int8 keeps deps light and avoids needing a GPU.
    return WhisperModel(_WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(audio_base64: str, mime_type: str) -> str | None:
    """
    Decode base64 audio and return local Whisper transcription, or None on failure.
    """
    mime = _normalize_mime(mime_type)
    ext = _EXT_BY_MIME.get(mime, ".ogg")

    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception as exc:
        logger.exception("[audio_transcribe] Invalid base64 audio: %s", exc)
        return None

    if not audio_bytes:
        logger.error("[audio_transcribe] Empty audio payload")
        return None

    try:
        model = _get_whisper_model()
    except Exception as exc:
        logger.exception(
            "[audio_transcribe] Failed to load Whisper model "
            "(install faster-whisper and ffmpeg): %s",
            exc,
        )
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()

            segments, _info = model.transcribe(tmp.name, beam_size=1)
            text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()

        if not text:
            logger.warning("[audio_transcribe] Whisper returned empty text")
            return None

        logger.info("[audio_transcribe] Transcribed %d chars from %s", len(text), mime)
        return text
    except Exception as exc:
        logger.exception("[audio_transcribe] Local Whisper failed: %s", exc)
        return None
