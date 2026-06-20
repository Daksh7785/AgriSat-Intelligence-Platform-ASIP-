from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime

from app.core.database import get_db
from app.services.water_service import WaterService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/water", tags=["Water Deficit Estimation"])

class DeficitRequest(BaseModel):
    field_id: int
    t_mean: float = 28.5
    t_max: float = 34.0
    t_min: float = 23.0
    wind_speed_2m: float = 2.1
    solar_rad: float = 22.0  # MJ/m^2/day
    rel_humidity: float = 65.0
    rainfall_mm: float = 0.0

@router.post("/deficit")
def calculate_water_deficit(
    req: DeficitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    field = db.query(models.Field).filter(models.Field.id == req.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    # Get latest crop classification and stage
    crop_info = db.query(models.CropClassification).filter(
        models.CropClassification.field_id == req.field_id
    ).order_by(models.CropClassification.classification_date.desc()).first()
    
    stage_info = db.query(models.PhenologicalStage).filter(
        models.PhenologicalStage.field_id == req.field_id
    ).order_by(models.PhenologicalStage.detection_date.desc()).first()
    
    crop_type = crop_info.crop_type if crop_info else "wheat"
    growth_stage = stage_info.stage if stage_info else "vegetative"
    
    # Get latest soil moisture reading
    latest_sm = db.query(models.SoilMoistureTimeSeries).filter(
        models.SoilMoistureTimeSeries.field_id == req.field_id
    ).order_by(models.SoilMoistureTimeSeries.timestamp.desc()).first()
    
    sm_frac = latest_sm.soil_moisture if latest_sm else 0.5
    
    # Calculate ET0
    et0 = WaterService.calculate_penman_monteith_et0(
        t_mean=req.t_mean,
        t_max=req.t_max,
        t_min=req.t_min,
        wind_speed_2m=req.wind_speed_2m,
        solar_rad=req.solar_rad,
        rel_humidity=req.rel_humidity
    )
    
    # Estimate Deficit
    results = WaterService.estimate_crop_water_deficit(
        et0=et0,
        crop_type=crop_type,
        growth_stage=growth_stage,
        soil_moisture_fraction=sm_frac,
        rainfall_mm=req.rainfall_mm
    )
    
    # Save to water deficit time series table
    db_ts = models.WaterDeficitTimeSeries(
        field_id=req.field_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        et0=results["et0"],
        etc=results["etc"],
        eta=results["eta"],
        water_deficit=results["water_deficit"],
        net_water_requirement=results["net_water_requirement"]
    )
    db.add(db_ts)
    db.commit()
    db.refresh(db_ts)
    
    return {
        "field_id": req.field_id,
        "timestamp": db_ts.timestamp.isoformat(),
        **results
    }
