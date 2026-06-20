from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import datetime

from app.core.database import get_db
from app.services.ingestion_service import IngestionService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/ingest", tags=["Ingestion Engine"])

class IngestRequest(BaseModel):
    sensor: str  # 'Sentinel-2', 'Sentinel-1', 'Landsat-8'
    start_date: str  # 'YYYY-MM-DD'
    end_date: str    # 'YYYY-MM-DD'
    bbox: Optional[List[float]] = [75.0, 30.0, 75.2, 30.2]

@router.post("/trigger")
def trigger_ingestion(
    req: IngestRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        start = datetime.datetime.strptime(req.start_date, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(req.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    try:
        rasters = IngestionService.trigger_temporal_ingestion(
            db=db,
            sensor=req.sensor,
            start_date=start,
            end_date=end,
            bbox=req.bbox
        )
        return {
            "status": "success",
            "message": f"Successfully ingested {len(rasters)} temporal median composites.",
            "rasters": [{"id": r.id, "name": r.name, "sensor": r.sensor, "date": r.acquisition_date.isoformat()} for r in rasters]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
