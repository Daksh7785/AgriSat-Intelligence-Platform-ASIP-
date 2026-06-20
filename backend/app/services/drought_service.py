from __future__ import annotations
import numpy as np
from sqlalchemy import text
from loguru import logger
from typing import Any

from app.db import models
from app.ml.drought.spei import compute_spei


class DroughtService:
    def __init__(self, db: Any):
        self.db = db

    async def compute_for_area(self, command_area_id: str, timescale_months: int = 3) -> dict:
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
            logger.warning(f"Command Area ID {command_area_id} not found in DB. Falling back to demo mode.")

        # Simulate a 36-month precipitation and PET series
        # In a real system, this queries the weather metrics table
        np.random.seed(ca_id if isinstance(ca_id, int) else 42)
        
        # Monthly precipitation (average central India: 80mm/month average, seasonal)
        months = 36
        precip = 80.0 + 70.0 * np.sin(np.arange(months) * 2 * np.pi / 12) + np.random.normal(0, 15, months)
        precip = np.clip(precip, 0.0, None)
        
        # PET (ET0) (average 100mm/month, peaking in summer)
        pet = 100.0 + 30.0 * np.sin(np.arange(months) * 2 * np.pi / 12 + np.pi/2) + np.random.normal(0, 5, months)
        pet = np.clip(pet, 10.0, None)

        # Inject a dry spell in the last 6 months (low precip, high pet)
        precip[-6:] = precip[-6:] * 0.25
        pet[-6:] = pet[-6:] * 1.3

        result = compute_spei(precip, pet, timescale_months=timescale_months)

        return {
            "command_area_id": command_area_id,
            "timescale_months": timescale_months,
            "latest_spei": float(result.spei_values[-1]),
            "latest_category": result.category[-1],
            "spei_series": result.spei_values.tolist(),
            "categories_series": result.category,
        }
