from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import datetime

from app.core.database import get_db
from app.services.stress_service import StressService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/stress", tags=["Moisture Stress Detection"])

class StressAnalysisRequest(BaseModel):
    field_id: int
    ndvi_anomaly: float = -0.1
    ndwi_anomaly: float = -0.05
    sar_moisture_index: float = -0.2
    rainfall_anomaly: float = -0.3
    temp_anomaly: float = 1.2

@router.post("/analyze")
def analyze_field_stress(
    req: StressAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    field = db.query(models.Field).filter(models.Field.id == req.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    # Run analysis
    res = StressService.detect_moisture_stress(
        ndvi_anomaly=req.ndvi_anomaly,
        ndwi_anomaly=req.ndwi_anomaly,
        sar_moisture_index=req.sar_moisture_index,
        rainfall_anomaly=req.rainfall_anomaly,
        temp_anomaly=req.temp_anomaly
    )
    
    # Store record
    # Deduce indices from anomalies
    ndvi = 0.5 + req.ndvi_anomaly
    ndwi = 0.3 + req.ndwi_anomaly
    sm = 0.5 + req.sar_moisture_index / 10.0 # scale to [0,1]
    
    db_stress = models.SoilMoistureTimeSeries(
        field_id=req.field_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        ndvi=float(ndvi),
        ndwi=float(ndwi),
        soil_moisture=float(np.clip(sm, 0.0, 1.0)),
        stress_level=res["stress_level"],
        stress_score=res["stress_score"]
    )
    db.add(db_stress)
    db.commit()
    db.refresh(db_stress)
    
    return {
        "field_id": req.field_id,
        "timestamp": db_stress.timestamp.isoformat(),
        "stress_level": db_stress.stress_level,
        "stress_score": db_stress.stress_score
    }

@router.get("/reports")
def get_village_stress_reports(
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    reports = StressService.generate_village_reports(db, district=district)
    return reports
