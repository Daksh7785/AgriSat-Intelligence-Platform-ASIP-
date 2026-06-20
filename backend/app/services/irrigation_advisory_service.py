from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from app.schemas.irrigation_advisory import IrrigationAdvisoryResponse, CommandAreaAdvisorySummary
from app.services.advisory_service import AdvisoryService

class IrrigationAdvisoryService:
    def __init__(self, db: Session):
        self.db = db

    async def get_latest_for_field(self, field_id: str) -> Optional[IrrigationAdvisoryResponse]:
        try:
            fid = int(field_id)
        except ValueError:
            field = self.db.query(models.Field).filter(models.Field.name == field_id).first()
            if not field:
                return None
            fid = field.id
            
        record = self.db.query(models.IrrigationAdvisory).filter(
            models.IrrigationAdvisory.field_id == fid
        ).order_by(desc(models.IrrigationAdvisory.timestamp)).first()
        
        if not record:
            return None
        return IrrigationAdvisoryResponse.model_validate(record)

    async def compute_command_area_advisory(
        self, command_area_id: str, as_of: Optional[date] = None
    ) -> CommandAreaAdvisorySummary:
        try:
            ca_id = int(command_area_id)
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.id == ca_id).first()
        except ValueError:
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.name == command_area_id).first()
            
        if not ca:
            raise ValueError(f"Command area {command_area_id} not found")
            
        fields = self.db.query(models.Field).filter(models.Field.command_area_id == ca.id).all()
        
        advisories = []
        total_req = 0.0
        total_sav = 0.0
        
        for field in fields:
            # Try to get latest existing advisory
            adv = self.db.query(models.IrrigationAdvisory).filter(
                models.IrrigationAdvisory.field_id == field.id
            ).order_by(desc(models.IrrigationAdvisory.timestamp)).first()
            
            if not adv:
                # Calculate fresh advisory
                crop_info = self.db.query(models.CropClassification).filter(
                    models.CropClassification.field_id == field.id
                ).order_by(desc(models.CropClassification.classification_date)).first()
                
                stage_info = self.db.query(models.PhenologicalStage).filter(
                    models.PhenologicalStage.field_id == field.id
                ).order_by(desc(models.PhenologicalStage.detection_date)).first()
                
                latest_sm = self.db.query(models.SoilMoistureTimeSeries).filter(
                    models.SoilMoistureTimeSeries.field_id == field.id
                ).order_by(desc(models.SoilMoistureTimeSeries.timestamp)).first()
                
                latest_deficit = self.db.query(models.WaterDeficitTimeSeries).filter(
                    models.WaterDeficitTimeSeries.field_id == field.id
                ).order_by(desc(models.WaterDeficitTimeSeries.timestamp)).first()
                
                crop_type = crop_info.crop_type if crop_info else "wheat"
                growth_stage = stage_info.stage if stage_info else "vegetative"
                sm_frac = latest_sm.soil_moisture if latest_sm else 0.5
                deficit_val = latest_deficit.water_deficit if latest_deficit else 1.5
                
                res = AdvisoryService.generate_irrigation_advisory(
                    crop_type=crop_type,
                    growth_stage=growth_stage,
                    soil_moisture_fraction=sm_frac,
                    water_deficit_mm=deficit_val,
                    forecast_rainfall_7d_mm=0.0
                )
                
                adv = models.IrrigationAdvisory(
                    field_id=field.id,
                    timestamp=datetime.utcnow(),
                    recommended_action=res["recommended_action"],
                    recommended_depth_mm=res["recommended_depth_mm"],
                    recommended_volume_m3=res["recommended_volume_m3"],
                    water_savings_m3=res["water_savings_m3"],
                    advisory_text=res["advisory_text"],
                    status="pending"
                )
                self.db.add(adv)
                self.db.commit()
                self.db.refresh(adv)
                
            advisories.append(IrrigationAdvisoryResponse.model_validate(adv))
            total_req += adv.recommended_volume_m3
            total_sav += adv.water_savings_m3
            
        return CommandAreaAdvisorySummary(
            command_area_id=str(ca.id),
            advisories=advisories,
            total_water_required_m3=total_req,
            potential_savings_m3=total_sav
        )

    async def aggregate_by_distributary(self, command_area_id: str) -> List[Dict[str, Any]]:
        try:
            ca_id = int(command_area_id)
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.id == ca_id).first()
        except ValueError:
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.name == command_area_id).first()
            
        if not ca:
            raise ValueError(f"Command area {command_area_id} not found")
            
        canals = self.db.query(models.Canal).filter(models.Canal.command_area_id == ca.id).all()
        fields = self.db.query(models.Field).filter(models.Field.command_area_id == ca.id).all()
        
        # If no canals, return empty list
        if not canals:
            return []
            
        # Map fields to canals (distributaries) by simple modulo
        canal_data = {c.id: {"canal_name": c.name, "flow_rate_cusec": c.flow_rate_cusec, "total_demand_m3": 0.0, "field_count": 0} for c in canals}
        
        for idx, field in enumerate(fields):
            canal = canals[idx % len(canals)]
            adv = self.db.query(models.IrrigationAdvisory).filter(
                models.IrrigationAdvisory.field_id == field.id
            ).order_by(desc(models.IrrigationAdvisory.timestamp)).first()
            
            demand = adv.recommended_volume_m3 if adv else 0.0
            canal_data[canal.id]["total_demand_m3"] += demand
            canal_data[canal.id]["field_count"] += 1
            
        return list(canal_data.values())
