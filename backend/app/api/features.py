from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import numpy as np

from app.core.database import get_db
from app.services.raster_service import RasterService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/features", tags=["Feature Extraction Engine"])

class ExtractRequest(BaseModel):
    field_id: int
    raster_id: int

class PhenologyRequest(BaseModel):
    doy: List[int]
    ndvi: List[float]

@router.post("/extract")
def extract_features(
    req: ExtractRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        stats = RasterService.extract_field_zonal_statistics(
            db_session=db,
            field_id=req.field_id,
            raster_id=req.raster_id
        )
        return {
            "field_id": req.field_id,
            "raster_id": req.raster_id,
            "features": stats
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/phenology/fit")
def fit_phenology(
    req: PhenologyRequest,
    current_user: models.User = Depends(get_current_user)
):
    if len(req.doy) != len(req.ndvi) or len(req.doy) < 4:
        raise HTTPException(status_code=400, detail="doy and ndvi must have same length and contain at least 4 observations.")
        
    try:
        days = np.array(req.doy)
        ndvi = np.array(req.ndvi)
        metrics = RasterService.fit_double_logistic(days, ndvi)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
