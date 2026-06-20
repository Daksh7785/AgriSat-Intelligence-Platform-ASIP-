"""
Irrigation Advisory API — exposes 8-day water deficit and advisory class per field
or per pixel-aggregated zone within a command area.
"""
from __future__ import annotations
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.schemas.irrigation_advisory import (
    IrrigationAdvisoryResponse, CommandAreaAdvisorySummary,
)
from app.services.irrigation_advisory_service import IrrigationAdvisoryService
from app.dependencies import get_db

router = APIRouter(prefix="/advisory", tags=["irrigation-advisory"])

ADVISORY_THRESHOLDS_MM = {
    "none": (0, 15),
    "light": (15, 30),
    "moderate": (30, 60),
    "critical": (60, float("inf")),
}


@router.get("/{command_area_id}/8day-map", response_model=CommandAreaAdvisorySummary)
async def get_8day_advisory_map(
    command_area_id: str,
    as_of: Optional[date] = Query(default=None, description="Defaults to latest cycle"),
    db=Depends(get_db),
):
    """Returns the field-level 8-day irrigation requirement map for a command area."""
    service = IrrigationAdvisoryService(db)
    try:
        result = await service.compute_command_area_advisory(command_area_id, as_of)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.get("/{field_id}/field", response_model=IrrigationAdvisoryResponse)
async def get_field_advisory(field_id: str, db=Depends(get_db)):
    """Returns the latest irrigation advisory for a single field."""
    service = IrrigationAdvisoryService(db)
    advisory = await service.get_latest_for_field(field_id)
    if advisory is None:
        raise HTTPException(status_code=404, detail="No advisory found for this field")
    return advisory


@router.get("/{command_area_id}/canal-schedule")
async def get_canal_schedule(command_area_id: str, db=Depends(get_db)):
    """
    Aggregates field-level irrigation requirement by distributary zone —
    feeds canal operator scheduling decisions.
    """
    service = IrrigationAdvisoryService(db)
    try:
        return await service.aggregate_by_distributary(command_area_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
