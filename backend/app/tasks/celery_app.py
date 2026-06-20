from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "agrisense_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Autodiscover tasks
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    imports=[
        "app.tasks.ingestion_tasks",
        "app.tasks.processing_tasks",
        "app.tasks.ml_tasks",
        "app.tasks.alert_tasks"
    ]
)
