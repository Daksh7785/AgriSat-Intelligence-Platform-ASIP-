from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ingestion_service import IngestionService
import datetime

@celery_app.task(name="tasks.ingestion.run_temporal_ingestion")
def run_temporal_ingestion_task(sensor: str, start_str: str, end_str: str, bbox: list):
    db = SessionLocal()
    try:
        start = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_str, "%Y-%m-%d").date()
        
        rasters = IngestionService.trigger_temporal_ingestion(
            db=db,
            sensor=sensor,
            start_date=start,
            end_date=end,
            bbox=bbox
        )
        return {"status": "success", "count": len(rasters)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
