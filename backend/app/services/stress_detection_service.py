from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from app.schemas.stress_assessment import StressMapResponse, FieldStressResponse

class StressDetectionService:
    def __init__(self, db: Session):
        self.db = db

    async def get_current_map(self, command_area_id: str) -> StressMapResponse:
        # Parse command area ID to int
        try:
            ca_id = int(command_area_id)
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.id == ca_id).first()
        except ValueError:
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.name == command_area_id).first()
            
        if not ca:
            raise ValueError(f"Command area {command_area_id} not found")
            
        # Get all fields in command area
        fields = self.db.query(models.Field).filter(models.Field.command_area_id == ca.id).all()
        field_ids = [f.id for f in fields]
        
        # Get latest soil moisture record for each field
        latest_records = []
        for fid in field_ids:
            rec = self.db.query(models.SoilMoistureTimeSeries).filter(
                models.SoilMoistureTimeSeries.field_id == fid
            ).order_by(desc(models.SoilMoistureTimeSeries.timestamp)).first()
            if rec:
                latest_records.append(rec)
                
        fields_response = []
        for r in latest_records:
            fields_response.append(FieldStressResponse.model_validate(r))
            
        return StressMapResponse(command_area_id=str(ca.id), fields=fields_response)

    async def get_timeseries(self, field_id: str, days_back: int) -> list[FieldStressResponse]:
        try:
            fid = int(field_id)
        except ValueError:
            # Maybe it's a uuid or name? Query field by name
            field = self.db.query(models.Field).filter(models.Field.name == field_id).first()
            if not field:
                return []
            fid = field.id
            
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        records = self.db.query(models.SoilMoistureTimeSeries).filter(
            models.SoilMoistureTimeSeries.field_id == fid,
            models.SoilMoistureTimeSeries.timestamp >= cutoff
        ).order_by(desc(models.SoilMoistureTimeSeries.timestamp)).all()
        
        return [FieldStressResponse.model_validate(r) for r in records]
