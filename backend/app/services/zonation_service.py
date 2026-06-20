from __future__ import annotations
import numpy as np
from sqlalchemy import text
from loguru import logger
from typing import Any

from app.db import models
from app.ml.zonation.subfield_zones import zone_field


class ZonationService:
    def __init__(self, db: Any):
        self.db = db

    async def get_zones(self, field_id: str) -> dict:
        try:
            f_id = int(field_id)
        except ValueError:
            f_id = 1

        # Check if field exists
        if hasattr(self.db, "execute"):
            res = await self.db.execute(text("SELECT id, name FROM fields WHERE id = :id"), {"id": f_id})
            field = res.first()
        else:
            field = self.db.query(models.Field).filter(models.Field.id == f_id).first()

        if not field:
            raise ValueError(f"Field with ID {field_id} not found")

        # For the demo/prototype, we generate a synthetic 10x10 field mask representing 100 pixels
        # 100 pixels at 10m Sentinel resolution corresponds to 1.0 hectare.
        np.random.seed(f_id)
        height, width = 10, 10
        field_mask = np.ones((height, width), dtype=bool)  # Entire 10x10 is inside field

        # Generate synthetic indexes
        # Add a clear two-zone pattern: left half has low VCI, right half has high VCI
        vci = np.zeros((height, width))
        vci[:, :5] = np.random.normal(0.3, 0.05, (height, 5))
        vci[:, 5:] = np.random.normal(0.8, 0.05, (height, 5))

        smi = np.zeros((height, width))
        smi[:, :5] = np.random.normal(0.25, 0.05, (height, 5))
        smi[:, 5:] = np.random.normal(0.7, 0.05, (height, 5))

        ndwi = np.zeros((height, width))
        ndwi[:, :5] = np.random.normal(0.15, 0.05, (height, 5))
        ndwi[:, 5:] = np.random.normal(0.45, 0.05, (height, 5))

        result = zone_field(field_mask, vci, smi, ndwi)

        return {
            "field_id": field_id,
            "n_zones": result.n_zones,
            "silhouette_score": result.silhouette_score,
            "zone_map": result.zone_map.tolist(),
            "zone_summary": result.zone_summary,
        }
