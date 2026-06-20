"""Uncertainty API — exposes confidence/entropy/disagreement layers for the map UI."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.services.uncertainty_service import UncertaintyService
from app.dependencies import get_db

router = APIRouter(prefix="/uncertainty", tags=["uncertainty"])


@router.get("/{command_area_id}/map")
async def get_uncertainty_map(command_area_id: str, db=Depends(get_db)):
    """Returns COG-tiled entropy and disagreement layers plus the review-priority mask."""
    service = UncertaintyService(db)
    try:
        res = await service.get_maps(command_area_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
