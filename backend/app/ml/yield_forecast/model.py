"""
Lightweight Yield Forecasting Model.

Method: regression of final yield (kg/ha) against two season-integral predictors,
both already computable from existing pipeline outputs:
  1. Cumulative NDVI integral over the season (proxy for total photosynthetic
     activity / biomass accumulation) — a well-established relationship in
     remote-sensing yield literature (e.g. Lobell et al., multiple crop-yield-NDVI
     integral studies).
  2. Accumulated Growing Degree Days at harvest (captures whether the season was
     thermally favorable or stressed, independent of vegetation greenness alone).

This is intentionally NOT a process-based crop simulator (DSSAT/APSIM) — it is a
fast, interpretable empirical model appropriate for a 30-hour prototype. The model
card must state this limitation explicitly: results are directional yield risk
indicators, not insurable-grade yield estimates, until validated against multi-season
ground-truth yield records.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from loguru import logger

# Indicative potential yields (kg/ha) used to express forecasts as "% of potential" —
# these are rough national averages and MUST be replaced with region/variety-specific
# values from the state agriculture department before any operational use.
POTENTIAL_YIELD_KG_HA = {
    "Wheat": 3500, "Rice/Paddy": 4000, "Cotton": 1800, "Sugarcane": 70000,
    "Maize": 3000, "Soybean": 1500, "Groundnut": 1800, "Mustard/Rapeseed": 1400,
}


@dataclass
class YieldForecast:
    crop_type: str
    predicted_yield_kg_ha: float
    pct_of_potential: float
    confidence_interval_kg_ha: tuple[float, float]
    risk_category: str   # "on_track" | "moderate_risk" | "high_risk"


class YieldForecastModel:
    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.residual_std: float = 0.0

    def train(
        self, ndvi_integral: np.ndarray, gdd_accumulated: np.ndarray, observed_yield_kg_ha: np.ndarray,
    ) -> dict:
        X = np.column_stack([ndvi_integral, gdd_accumulated])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, observed_yield_kg_ha)
        self.is_trained = True

        preds = self.model.predict(X_scaled)
        residuals = observed_yield_kg_ha - preds
        self.residual_std = float(np.std(residuals))

        metrics = {
            "r2": float(r2_score(observed_yield_kg_ha, preds)),
            "mae_kg_ha": float(mean_absolute_error(observed_yield_kg_ha, preds)),
            "n_samples": int(len(observed_yield_kg_ha)),
            "residual_std_kg_ha": self.residual_std,
        }
        logger.info(f"Yield model trained — R2={metrics['r2']:.3f}, MAE={metrics['mae_kg_ha']:.0f} kg/ha")
        return metrics

    def predict(
        self, ndvi_integral: float, gdd_accumulated: float, crop_type: str,
    ) -> YieldForecast:
        if not self.is_trained:
            raise ValueError("Model not trained — call train() first")

        X = self.scaler.transform([[ndvi_integral, gdd_accumulated]])
        pred = float(self.model.predict(X)[0])
        pred = max(pred, 0.0)

        potential = POTENTIAL_YIELD_KG_HA.get(crop_type, pred / 0.75)
        pct_of_potential = (pred / potential) * 100 if potential > 0 else 0.0

        ci_low = max(0.0, pred - 1.96 * self.residual_std)
        ci_high = pred + 1.96 * self.residual_std

        if pct_of_potential >= 85:
            risk = "on_track"
        elif pct_of_potential >= 65:
            risk = "moderate_risk"
        else:
            risk = "high_risk"

        return YieldForecast(
            crop_type=crop_type,
            predicted_yield_kg_ha=round(pred, 1),
            pct_of_potential=round(pct_of_potential, 1),
            confidence_interval_kg_ha=(round(ci_low, 1), round(ci_high, 1)),
            risk_category=risk,
        )
