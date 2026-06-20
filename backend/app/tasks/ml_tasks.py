from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ml_service import AutoMLCropClassifier
import numpy as np

@celery_app.task(name="tasks.ml.train_ensemble")
def train_ensemble_task(features_list: list, labels: list):
    """Asynchronous AutoML classifier training."""
    try:
        X = np.array(features_list) # shape: (samples, seq_len, input_dim)
        y = np.array(labels)
        
        classifier = AutoMLCropClassifier(seq_len=X.shape[1], input_dim=X.shape[2])
        classifier.train(X, y)
        return {"status": "success", "message": "Ensemble classifier successfully trained."}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
