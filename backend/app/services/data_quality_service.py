from __future__ import annotations
import numpy as np
from sqlalchemy import text
from loguru import logger
from typing import Any
from datetime import date, timedelta

from app.db import models
from app.data.cloud_triage_logger import decide, summarize_season, TriageDecision


class DataQualityService:
    def __init__(self, db: Any):
        self.db = db

    async def get_triage_summary(self, command_area_id: str) -> dict:
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

        # Simulate a sequence of 10 satellite acquisitions (e.g. Sentinel-2 pass every 5 days)
        np.random.seed(ca_id if isinstance(ca_id, int) else 42)
        base_date = date(2026, 1, 1)
        
        decisions = []
        for i in range(12):
            acq_date = base_date + timedelta(days=5 * i)
            # Make some scenes cloudy
            cloud_pct = float(np.random.choice([
                np.random.uniform(0, 5),   # clear
                np.random.uniform(15, 30), # partial
                np.random.uniform(60, 95), # heavy cloud
            ], p=[0.5, 0.3, 0.2]))
            
            # S1 SAR is dual-orbit and generally available
            sar_avail = bool(np.random.choice([True, False], p=[0.9, 0.1]))
            
            d = decide(acq_date, command_area_id, cloud_pct, sar_avail)
            decisions.append(d)

        summary = summarize_season(decisions)

        return {
            "command_area_id": command_area_id,
            "total_acquisitions": summary["total_acquisitions"],
            "pct_sar_fallback_or_blend": summary["pct_sar_fallback_or_blend"],
            "data_gaps": summary["data_gaps"],
            "triage_log": [
                {
                    "acquisition_date": d.acquisition_date.isoformat(),
                    "cloud_cover_pct": d.cloud_cover_pct,
                    "sar_available": d.sar_available,
                    "decision": d.decision,
                    "reasoning": d.reasoning
                } for d in decisions
            ],
            "summary_counts": summary["decision_counts"]
        }
