"""Phenology API — current growth stage and stage history per field."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.common import PhenologyResponse
from app.services.phenology_service import PhenologyService
from app.dependencies import get_db

router = APIRouter(prefix="/phenology", tags=["phenology"])


@router.get("/{field_id}/current", response_model=PhenologyResponse)
async def get_current_stage(field_id: str, db=Depends(get_db)):
    """Returns current phenological stage, days since sowing, and accumulated GDD."""
    service = PhenologyService(db)
    record = await service.get_current_stage(field_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No phenology record for this field")
    return record


@router.get("/{field_id}/calendar")
async def get_phenology_calendar(field_id: str, db=Depends(get_db)):
    """Returns the projected stage transition calendar for the current season."""
    service = PhenologyService(db)
    return await service.get_projected_calendar(field_id)
