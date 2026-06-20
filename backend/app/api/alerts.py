from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.alert_service import AlertService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/alerts", tags=["Alert System"])

@router.get("/list")
def list_alerts(
    status: Optional[str] = "unread",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Alert)
    if status:
        query = query.filter(models.Alert.status == status)
    alerts = query.order_by(models.Alert.sent_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "field_id": a.field_id,
            "trigger_type": a.trigger_type,
            "severity": a.severity,
            "message": a.message,
            "sent_at": a.sent_at.isoformat(),
            "status": a.status
        } for a in alerts
    ]

@router.post("/read/{alert_id}")
def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.status = "read"
    db.commit()
    return {"status": "success", "message": f"Alert {alert_id} marked as read."}

@router.post("/trigger/{field_id}")
def trigger_alert_processing(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    field = db.query(models.Field).filter(models.Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
        
    try:
        count = AlertService.process_field_alerts(db, field_id)
        return {
            "status": "success",
            "message": f"Processed alert thresholds for field {field_id}. Triggered {count} new alerts."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
