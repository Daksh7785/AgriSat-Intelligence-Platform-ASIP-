from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime

from app.core.database import get_db
from app.services.advisory_service import AdvisoryService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/advisory", tags=["Irrigation Advisory"])

class AdvisoryRequest(BaseModel):
    field_id: int
    forecast_rainfall_7d_mm: float = 0.0

@router.post("/generate")
def generate_advisory(
    req: AdvisoryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    field = db.query(models.Field).filter(models.Field.id == req.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    # Get latest crop type, stage, moisture deficit and soil moisture
    crop_info = db.query(models.CropClassification).filter(
        models.CropClassification.field_id == req.field_id
    ).order_by(models.CropClassification.classification_date.desc()).first()
    
    stage_info = db.query(models.PhenologicalStage).filter(
        models.PhenologicalStage.field_id == req.field_id
    ).order_by(models.PhenologicalStage.detection_date.desc()).first()
    
    latest_sm = db.query(models.SoilMoistureTimeSeries).filter(
        models.SoilMoistureTimeSeries.field_id == req.field_id
    ).order_by(models.SoilMoistureTimeSeries.timestamp.desc()).first()
    
    latest_deficit = db.query(models.WaterDeficitTimeSeries).filter(
        models.WaterDeficitTimeSeries.field_id == req.field_id
    ).order_by(models.WaterDeficitTimeSeries.timestamp.desc()).first()
    
    crop_type = crop_info.crop_type if crop_info else "wheat"
    growth_stage = stage_info.stage if stage_info else "vegetative"
    sm_frac = latest_sm.soil_moisture if latest_sm else 0.5
    deficit_val = latest_deficit.water_deficit if latest_deficit else 1.5
    
    # Calculate advisory
    res = AdvisoryService.generate_irrigation_advisory(
        crop_type=crop_type,
        growth_stage=growth_stage,
        soil_moisture_fraction=sm_frac,
        water_deficit_mm=deficit_val,
        forecast_rainfall_7d_mm=req.forecast_rainfall_7d_mm
    )
    
    # Save advisory to DB
    db_adv = models.IrrigationAdvisory(
        field_id=req.field_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        recommended_action=res["recommended_action"],
        recommended_depth_mm=res["recommended_depth_mm"],
        recommended_volume_m3=res["recommended_volume_m3"],
        water_savings_m3=res["water_savings_m3"],
        advisory_text=res["advisory_text"],
        status="sent",
        sent_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(db_adv)
    db.commit()
    db.refresh(db_adv)
    
    return {
        "id": db_adv.id,
        "field_id": req.field_id,
        "timestamp": db_adv.timestamp.isoformat(),
        **res
    }

@router.get("/list/{field_id}")
def list_advisories(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    advisories = db.query(models.IrrigationAdvisory).filter(
        models.IrrigationAdvisory.field_id == field_id
    ).order_by(models.IrrigationAdvisory.timestamp.desc()).all()
    
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "recommended_action": a.recommended_action,
            "recommended_depth_mm": a.recommended_depth_mm,
            "recommended_volume_m3": a.recommended_volume_m3,
            "water_savings_m3": a.water_savings_m3,
            "advisory_text": a.advisory_text,
            "status": a.status
        } for a in advisories
    ]
