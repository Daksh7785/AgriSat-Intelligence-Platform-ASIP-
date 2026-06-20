"""Crop rotation tracking API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.rotation_tracker_db_service import RotationTrackerDBService
from app.dependencies import get_db

router = APIRouter(prefix="/rotation", tags=["rotation"])


@router.get("/{field_id}/history")
async def get_rotation_history(field_id: str, db=Depends(get_db)):
    """Returns the field's multi-season crop classification history with rotation flags."""
    service = RotationTrackerDBService(db)
    try:
        res = await service.get_report(field_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
