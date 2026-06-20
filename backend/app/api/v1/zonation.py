"""Sub-field zonation API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.zonation_service import ZonationService
from app.dependencies import get_db

router = APIRouter(prefix="/zonation", tags=["zonation"])


@router.get("/{field_id}/zones")
async def get_subfield_zones(field_id: str, db=Depends(get_db)):
    """Returns the 2-4 internal management zones for this field with per-zone stats,
    worst zone first, so the advisory can target irrigation to the part of the field
    that actually needs it."""
    service = ZonationService(db)
    try:
        res = await service.get_zones(field_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
