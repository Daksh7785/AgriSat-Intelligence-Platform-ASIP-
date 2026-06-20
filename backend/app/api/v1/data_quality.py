"""Data quality / triage transparency API — surfaces the cloud-cover decision log."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.data_quality_service import DataQualityService
from app.dependencies import get_db

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.get("/{command_area_id}/triage-log")
async def get_triage_log(command_area_id: str, db=Depends(get_db)):
    """Returns the per-acquisition cloud/SAR triage decision history for this command
    area, plus a season summary — the audit trail behind the 'all-weather monitoring' claim."""
    service = DataQualityService(db)
    try:
        res = await service.get_triage_summary(command_area_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
