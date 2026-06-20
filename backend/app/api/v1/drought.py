"""Drought API — exposes SPEI drought classification per command area."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.drought_service import DroughtService
from app.dependencies import get_db

router = APIRouter(prefix="/drought", tags=["drought"])


@router.get("/{command_area_id}/spei")
async def get_spei(
    command_area_id: str,
    timescale_months: int = Query(default=3, ge=1, le=12),
    db=Depends(get_db),
):
    """Returns the SPEI drought series and current category for the command area."""
    service = DroughtService(db)
    try:
        res = await service.compute_for_area(command_area_id, timescale_months)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
