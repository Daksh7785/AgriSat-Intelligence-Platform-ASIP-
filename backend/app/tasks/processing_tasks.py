from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.raster_service import RasterService

@celery_app.task(name="tasks.processing.extract_field_features")
def extract_field_features_task(field_id: int, raster_id: int):
    db = SessionLocal()
    try:
        stats = RasterService.extract_field_zonal_statistics(
            db_session=db,
            field_id=field_id,
            raster_id=raster_id
        )
        return {"status": "success", "field_id": field_id, "stats": stats}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
