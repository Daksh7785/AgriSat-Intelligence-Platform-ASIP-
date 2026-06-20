"""Explainability API — exposes per-pixel and per-field SHAP explanations."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.common import PixelExplanationResponse
from app.services.explainability_service import ExplainabilityService
from app.dependencies import get_db

router = APIRouter(prefix="/explain", tags=["explainability"])


@router.get("/{field_id}/why", response_model=PixelExplanationResponse)
async def explain_field_classification(field_id: str, db=Depends(get_db)):
    """
    Returns a human-readable explanation of why this field was classified as its
    predicted crop type, with the top contributing features and their SHAP values.
    """
    service = ExplainabilityService(db)
    try:
        explanation = await service.explain_field(field_id)
        return explanation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
