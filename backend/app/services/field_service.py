from __future__ import annotations
from sqlalchemy import text
from loguru import logger
from typing import Any
import numpy as np

from app.db import models
from app.services.roi_calculator_service import compute_cycle_savings, aggregate_seasonal_savings


class FieldService:
    def __init__(self, db: Any):
        self.db = db

    async def compute_season_savings(self, field_id: str) -> dict:
        try:
            f_id = int(field_id)
        except ValueError:
            f_id = 1

        # Query field
        if hasattr(self.db, "execute"):
            res = await self.db.execute(text("SELECT id, name FROM fields WHERE id = :id"), {"id": f_id})
            field = res.first()
        else:
            field = self.db.query(models.Field).filter(models.Field.id == f_id).first()

        if not field:
            raise ValueError(f"Field with ID {field_id} not found")

        # Query advisories
        if hasattr(self.db, "execute"):
            res_advisories = await self.db.execute(
                text("SELECT recommended_depth_mm, water_savings_m3 FROM irrigation_advisories WHERE field_id = :id"),
                {"id": f_id}
            )
            advisories = res_advisories.fetchall()
        else:
            advisories = self.db.query(models.IrrigationAdvisory).filter(models.IrrigationAdvisory.field_id == f_id).all()

        # If no advisories, generate synthetic ones for demo mode
        if not advisories:
            cycles = 5
            cycle_results = []
            for i in range(cycles):
                req_mm = float(20.0 + 10.0 * np.sin(i))
                c_save = compute_cycle_savings(req_mm, field_area_hectares=1.2)
                cycle_results.append(c_save)
            agg = aggregate_seasonal_savings(cycle_results)
            return {
                "field_id": field_id,
                "n_cycles": agg["n_cycles"],
                "total_water_saved_liters": agg["total_water_saved_liters"],
                "total_cost_saved_rs": agg["total_cost_saved_rs"],
                "demo_mode": True,
            }

        # Calculate from advisories
        total_water_saved_m3 = sum(float(a[1]) if isinstance(a, tuple) else float(a.water_savings_m3) for a in advisories)
        total_water_saved_liters = total_water_saved_m3 * 1000.0
        # Cost is water * cost per m3
        cost_per_m3 = 1.8
        total_cost_saved_rs = total_water_saved_m3 * cost_per_m3

        return {
            "field_id": field_id,
            "n_cycles": len(advisories),
            "total_water_saved_liters": round(total_water_saved_liters, 1),
            "total_cost_saved_rs": round(total_cost_saved_rs, 2),
            "demo_mode": False,
        }
