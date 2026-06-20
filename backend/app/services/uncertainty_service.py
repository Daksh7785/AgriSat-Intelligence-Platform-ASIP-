from __future__ import annotations
import numpy as np
from sqlalchemy import text
from loguru import logger
from typing import Any

from app.db import models
from app.ml.crop_classifier.uncertainty import build_uncertainty_maps


class UncertaintyService:
    def __init__(self, db: Any):
        self.db = db

    async def get_maps(self, command_area_id: str) -> dict:
        # Check if the command area exists
        try:
            ca_id = int(command_area_id)
        except ValueError:
            ca_id = 1

        if hasattr(self.db, "execute"):
            res = await self.db.execute(text("SELECT id, name FROM command_areas WHERE id = :id"), {"id": ca_id})
            ca = res.first()
        else:
            ca = self.db.query(models.CommandArea).filter(models.CommandArea.id == ca_id).first()

        if not ca:
            # For demonstration, we allow fallback
            logger.warning(f"Command Area ID {command_area_id} not found in DB. Running in demo fallback mode.")

        # Simulate two 20x20 arrays of class probabilities (e.g. 5 crop classes)
        height, width, n_classes = 20, 20, 5
        np.random.seed(ca_id if isinstance(ca_id, int) else 42)

        # Generate random probabilities that sum to 1
        rf_raw = np.random.dirichlet(np.ones(n_classes), size=(height, width))
        xgb_raw = np.random.dirichlet(np.ones(n_classes), size=(height, width))

        # Run uncertainty calculation
        maps = build_uncertainty_maps(rf_raw, xgb_raw)

        return {
            "command_area_id": command_area_id,
            "entropy_map": maps.entropy_map.tolist(),
            "disagreement_map": maps.disagreement_map.tolist(),
            "review_priority_mask": maps.review_priority_mask.tolist(),
        }
