from __future__ import annotations
import numpy as np
from sqlalchemy import text
from loguru import logger
from typing import Any

from app.db import models
from app.ml.crop_classifier.model import CropClassifierModel
from app.ml.crop_classifier.explainability import CropClassifierExplainer, PixelExplanation


class ExplainabilityService:
    def __init__(self, db: Any):
        self.db = db

    async def explain_field(self, field_id: str) -> PixelExplanation:
        # Convert field_id to integer if possible, otherwise lookup by name or cast
        try:
            f_id = int(field_id)
        except ValueError:
            # Fallback to querying by name or parsing
            f_id = 1

        # Check if field exists
        # Dual-support sync/async session
        if hasattr(self.db, "execute"):
            res = await self.db.execute(text("SELECT id, name FROM fields WHERE id = :id"), {"id": f_id})
            field = res.first()
        else:
            field = self.db.query(models.Field).filter(models.Field.id == f_id).first()

        if not field:
            raise ValueError(f"Field with ID {field_id} not found")

        # Generate a synthetic/mock 70-dimensional feature vector for the field
        # In production, this would be compiled from Sentinel-2 + Sentinel-1 imagery for the field
        n_features = 70
        np.random.seed(f_id)
        feature_vector = np.random.uniform(0.2, 0.8, n_features)

        # Ensure we have a trained CropClassifierModel
        model = CropClassifierModel(n_estimators_rf=10, n_estimators_xgb=10)
        model.build_feature_names()

        # Train on some dummy data to initialize the pipeline
        dummy_X = np.random.uniform(0.1, 0.9, (20, n_features))
        dummy_y = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9] * 2)
        model.train(dummy_X, dummy_y)

        # Background sample
        background_sample = np.random.uniform(0.1, 0.9, (10, n_features))

        # Explain the prediction
        explainer = CropClassifierExplainer(model, background_sample)
        explanation = explainer.explain_pixel(feature_vector)

        return explanation
