"""
Early-Warning Lead-Time Scorer.

Retrospectively measures how many days/composites before a "visible" stress signal
(a sharp NDVI drop, used as a proxy for what a farmer would notice by eye) the
SAR-inclusive stress detector first flagged moderate-or-worse stress.

This validates (or corrects) any "N days early warning" claim made in the pitch —
run it once against the historical sample data and report the ACTUAL measured
lead time, not an assumed one.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional
import numpy as np
from loguru import logger


@dataclass
class LeadTimeResult:
    visible_crash_date: Optional[date]
    earliest_detector_flag_date: Optional[date]
    lead_time_days: Optional[int]
    detector_signal_used: str   # "smi" | "vh_backscatter" | "vci"


def find_visible_ndvi_crash(
    dates: list[date], ndvi_series: np.ndarray, drop_thresh: float = 0.15,
) -> Optional[date]:
    """A 'visible' crash: an NDVI drop a farmer would notice without instruments —
    defined here as a single-composite drop exceeding drop_thresh."""
    diffs = np.diff(ndvi_series)
    crash_indices = np.where(diffs <= -drop_thresh)[0]
    if len(crash_indices) == 0:
        return None
    return dates[crash_indices[0] + 1]


def find_earliest_stress_flag(
    dates: list[date], stress_level_series: list[str], min_level: str = "moderate",
) -> Optional[date]:
    severity_rank = {"none": 0, "mild": 1, "moderate": 2, "severe": 3, "No Stress": 0, "Mild Stress": 1, "Moderate Stress": 2, "Severe Stress": 3, "Critical Stress": 4}
    threshold = severity_rank.get(min_level, 2)
    for d, level in zip(dates, stress_level_series):
        if severity_rank.get(level, 0) >= threshold:
            return d
    return None


def score_lead_time(
    dates: list[date],
    ndvi_series: np.ndarray,
    stress_level_series: list[str],
    detector_signal_used: str = "smi+vci",
) -> LeadTimeResult:
    crash_date = find_visible_ndvi_crash(dates, ndvi_series)
    flag_date = find_earliest_stress_flag(dates, stress_level_series)

    lead_time_days = None
    if crash_date is not None and flag_date is not None:
        lead_time_days = (crash_date - flag_date).days
        if lead_time_days < 0:
            logger.warning(
                f"Detector flagged AFTER the visible crash (lead_time={lead_time_days}d) "
                f"— this run does not support an 'early warning' claim for this field"
            )
        else:
            logger.info(f"Measured lead time: {lead_time_days} days before visible crash")
    else:
        logger.info("Could not measure lead time — no crash or no stress flag found in series")

    return LeadTimeResult(
        visible_crash_date=crash_date,
        earliest_detector_flag_date=flag_date,
        lead_time_days=lead_time_days,
        detector_signal_used=detector_signal_used,
    )


def aggregate_lead_time_report(results: list[LeadTimeResult]) -> dict:
    """Run across many fields/seasons and report the honest distribution, not a single
    cherry-picked number, for the model card / presentation slide."""
    valid = [r.lead_time_days for r in results if r.lead_time_days is not None and r.lead_time_days >= 0]
    if not valid:
        return {"n_measured": 0, "median_lead_time_days": None, "note": "insufficient data"}
    return {
        "n_measured": len(valid),
        "median_lead_time_days": float(np.median(valid)),
        "p25_lead_time_days": float(np.percentile(valid, 25)),
        "p75_lead_time_days": float(np.percentile(valid, 75)),
    }
