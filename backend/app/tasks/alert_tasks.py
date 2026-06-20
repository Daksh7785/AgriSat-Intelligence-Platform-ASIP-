from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.alert_service import AlertService
from app.db import models

@celery_app.task(name="tasks.alert.check_all_fields")
def check_all_fields_alerts_task():
    db = SessionLocal()
    try:
        fields = db.query(models.Field).all()
        total_alerts = 0
        for f in fields:
            alerts_triggered = AlertService.process_field_alerts(db, f.id)
            total_alerts += alerts_triggered
        return {"status": "success", "alerts_triggered": total_alerts}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
