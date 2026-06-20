"""
Sowing Date Detector.

Detects sowing date per field from a multi-temporal NDVI + SAR backscatter
time series using two independent signals, cross-validated against each other:

  1. Optical: first sustained NDVI rise from a soil-baseline plateau
     (NDVI < 0.3 for >= 2 consecutive composites, followed by a rise of
     >= 0.1 over the next 2-3 composites that does not revert).
  2. SAR: a backscatter DROP in VV (tillage roughens then smooths the soil,
     and ponding/transplanting in paddy systems lowers VV) that precedes
     the optical NDVI rise by 1-3 composites — used as a cloud-robust
     cross-check during kharif when optical may be the lagging signal.

If the two disagree by more than one compositing window, the optical signal
is trusted by default (documented assumption) and the disagreement is logged
for manual review — this prevents a single noisy index from silently setting
every downstream phenology stage and GDD calculation incorrectly.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
import numpy as np
from loguru import logger


@dataclass
class SowingDateResult:
    sowing_date: Optional[date]
    method: str                     # "optical" | "sar" | "disagreement_optical_default"
    confidence: float
    optical_estimate: Optional[date]
    sar_estimate: Optional[date]


def detect_sowing_date_optical(
    dates: list[date], ndvi_series: np.ndarray,
    baseline_thresh: float = 0.3, rise_thresh: float = 0.1,
) -> Optional[date]:
    n = len(ndvi_series)
    for i in range(2, n - 2):
        baseline_ok = np.all(ndvi_series[max(0, i - 2):i] < baseline_thresh)
        rise_ok = (ndvi_series[min(i + 2, n - 1)] - ndvi_series[i]) >= rise_thresh
        sustained = ndvi_series[min(i + 3, n - 1)] >= ndvi_series[i]  # doesn't revert
        if baseline_ok and rise_ok and sustained:
            return dates[i]
    return None


def detect_sowing_date_sar(
    dates: list[date], vv_series_db: np.ndarray, drop_thresh_db: float = -2.0,
) -> Optional[date]:
    diffs = np.diff(vv_series_db)
    for i, d in enumerate(diffs):
        if d <= drop_thresh_db:
            return dates[i + 1]
    return None


def detect_sowing_date(
    dates: list[date],
    ndvi_series: np.ndarray,
    vv_series_db: Optional[np.ndarray] = None,
    max_disagreement_composites: int = 1,
    composite_interval_days: int = 8,
) -> SowingDateResult:
    optical_date = detect_sowing_date_optical(dates, ndvi_series)

    if vv_series_db is None:
        return SowingDateResult(
            sowing_date=optical_date, method="optical", confidence=0.7,
            optical_estimate=optical_date, sar_estimate=None,
        )

    sar_date = detect_sowing_date_sar(dates, vv_series_db)

    if optical_date is None and sar_date is None:
        logger.warning("Sowing date undetectable from either optical or SAR signal")
        return SowingDateResult(None, "none", 0.0, None, None)

    if optical_date is None:
        return SowingDateResult(sar_date, "sar", 0.6, None, sar_date)
    if sar_date is None:
        return SowingDateResult(optical_date, "optical", 0.7, optical_date, None)

    disagreement_days = abs((optical_date - sar_date).days)
    max_allowed = max_disagreement_composites * composite_interval_days

    if disagreement_days <= max_allowed:
        # Agreement: average the two estimates, weighted toward optical
        avg_date = optical_date + timedelta(days=int(0.6 * (sar_date - optical_date).days))
        return SowingDateResult(avg_date, "optical+sar_agree", 0.9, optical_date, sar_date)

    logger.warning(
        f"Sowing date disagreement: optical={optical_date}, sar={sar_date}, "
        f"diff={disagreement_days}d > {max_allowed}d threshold. Defaulting to optical."
    )
    return SowingDateResult(
        optical_date, "disagreement_optical_default", 0.5, optical_date, sar_date,
    )
