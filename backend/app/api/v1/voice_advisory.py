"""Voice advisory API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.voice_advisory_service import VoiceAdvisoryService
from app.services.notification_service import NotificationService
from app.dependencies import get_db

router = APIRouter(prefix="/voice", tags=["voice-advisory"])


@router.get("/{field_id}/audio")
async def get_voice_advisory(field_id: str, language: str = "hi", db=Depends(get_db)):
    """Generates (or returns cached) audio advisory for this field's latest irrigation recommendation."""
    notif_service = NotificationService(db)
    voice_service = VoiceAdvisoryService()
    try:
        text = await notif_service.get_latest_advisory_text(field_id, language)
        result = voice_service.generate(text, language, advisory_id=field_id)
        return {"audio_url": result.audio_path, "language": result.language,
                "duration_seconds": result.duration_estimate_seconds}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
