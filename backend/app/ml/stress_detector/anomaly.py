"""
NDVI Anomaly Detector — flags stress relative to a pixel's own historical baseline
rather than an absolute threshold.

z_anomaly = (NDVI_current - NDVI_historical_mean) / NDVI_historical_std

This catches two cases a static threshold misses:
  1. A naturally low-NDVI field (e.g. light soil, sparse stand) that is actually
     healthy for itself but would trip an absolute "low NDVI = stress" rule.
  2. A naturally high-NDVI field that drops to a still-decent absolute value but
     is significantly below ITS OWN normal — an early signal a static threshold
     would miss entirely.

Requires at minimum 3 years of same-period historical composites per pixel to
produce a stable mean/std; with fewer years, falls back to a regional baseline
(same crop type, same growth stage, across the command area) with a logged caveat.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger

ANOMALY_THRESHOLDS = {
    "severe_negative": -2.0,
    "moderate_negative": -1.0,
    "normal_low": -0.5,
    "normal_high": 0.5,
    "moderate_positive": 1.0,
}


@dataclass
class AnomalyResult:
    z_score: np.ndarray            # H x W
    category: np.ndarray           # H x W, string labels via np.where chaining
    used_regional_fallback: bool
    n_historical_years: int


def compute_pixel_anomaly(
    current_ndvi: np.ndarray,                 # H x W
    historical_ndvi_stack: np.ndarray,         # n_years x H x W (same period, prior years)
    min_years_for_pixelwise: int = 3,
) -> AnomalyResult:
    n_years = historical_ndvi_stack.shape[0]
    used_fallback = n_years < min_years_for_pixelwise

    if used_fallback:
        logger.warning(
            f"Only {n_years} historical years available (<{min_years_for_pixelwise}) — "
            f"falling back to scene-wide regional baseline instead of per-pixel history"
        )
        hist_mean = np.nanmean(historical_ndvi_stack)
        hist_std = np.nanstd(historical_ndvi_stack) + 1e-6
        z_score = (current_ndvi - hist_mean) / hist_std
    else:
        hist_mean = np.nanmean(historical_ndvi_stack, axis=0)
        hist_std = np.nanstd(historical_ndvi_stack, axis=0) + 1e-6
        z_score = (current_ndvi - hist_mean) / hist_std

    category = np.full(z_score.shape, "normal", dtype=object)
    category[z_score <= ANOMALY_THRESHOLDS["severe_negative"]] = "severe_negative_anomaly"
    category[(z_score > ANOMALY_THRESHOLDS["severe_negative"]) &
              (z_score <= ANOMALY_THRESHOLDS["moderate_negative"])] = "moderate_negative_anomaly"
    category[z_score >= ANOMALY_THRESHOLDS["moderate_positive"]] = "positive_anomaly"

    n_flagged = np.sum(z_score <= ANOMALY_THRESHOLDS["moderate_negative"])
    logger.info(f"NDVI anomaly computed — {n_flagged} pixels flagged as negative anomaly "
                f"(fallback={used_fallback})")

    return AnomalyResult(
        z_score=z_score, category=category,
        used_regional_fallback=used_fallback, n_historical_years=n_years,
    )
