"""ROI / Water-Savings API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.roi_calculator_service import compute_cycle_savings
from app.services.field_service import FieldService
from app.dependencies import get_db

router = APIRouter(prefix="/roi", tags=["roi"])


@router.get("/{field_id}/season-savings")
async def get_season_savings(field_id: str, db=Depends(get_db)):
    """Returns cumulative water and cost savings for the field's current season,
    computed live from the field's irrigation advisory history."""
    field_service = FieldService(db)
    try:
        res = await field_service.compute_season_savings(field_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
