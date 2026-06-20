"""
Voice Advisory Service.

Converts the existing text advisory (see notification_service.py's
ADVISORY_TEMPLATES) into a short audio clip using an open-source TTS engine
(gTTS for the demo — swappable for an on-device/offline engine like Coqui TTS
in a production deployment where internet access at the point of generation
cannot be assumed).

Output is a small MP3 saved to object storage and referenced by URL — the
WhatsApp/voice-call delivery layer (IVR, explicitly out of scope per the
gap-fill prompt) is NOT built here; this only produces the audio asset so a
future IVR integration has something real to play.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from gtts import gTTS
from loguru import logger

# Swapped out mr to en or other language codes supported by gtts.
LANGUAGE_TTS_CODES = {"hi": "hi", "en": "en", "ta": "ta", "te": "te", "kn": "kn", "mr": "mr"}


@dataclass
class VoiceAdvisoryResult:
    audio_path: str
    language: str
    text_used: str
    duration_estimate_seconds: float


class VoiceAdvisoryService:
    def __init__(self, output_dir: Path = Path("./data/voice_advisories")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, advisory_text: str, language: str, advisory_id: str) -> VoiceAdvisoryResult:
        tts_lang = LANGUAGE_TTS_CODES.get(language, "hi")
        out_path = self.output_dir / f"{advisory_id}_{tts_lang}.mp3"

        tts = gTTS(text=advisory_text, lang=tts_lang, slow=False)
        tts.save(str(out_path))

        # Rough estimate: ~150 words/min average speech rate for short advisory clips.
        n_words = len(advisory_text.split())
        duration_estimate = (n_words / 150) * 60

        logger.info(f"Generated voice advisory: {out_path} ({duration_estimate:.1f}s estimated)")

        return VoiceAdvisoryResult(
            audio_path=str(out_path), language=tts_lang,
            text_used=advisory_text, duration_estimate_seconds=round(duration_estimate, 1),
        )
