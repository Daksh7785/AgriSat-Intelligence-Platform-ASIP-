"""
Crop Rotation / Fallow-Cycle Tracker.

The problem statement explicitly requires using the previous season's crop
classification as an input signal for the current season — this module is the
natural second half of that requirement: once you have N seasons of classified
history for a field, track the rotation pattern and flag agronomically meaningful
repetition.

Flags raised:
  - SAME_CROP_REPEATED: identical crop type for 3+ consecutive seasons — associated
    with soil nutrient depletion and pest/pathogen buildup risk for many crops
    (well-dominated agronomic concern, e.g. continuous rice or continuous cotton).
  - NO_FALLOW_OBSERVED: no fallow/rest season detected across the tracked window —
    relevant to soil health monitoring programmes under NMSA.
  - ROTATION_BREAK: a field that had a consistent rotation pattern (e.g. wheat-rice
    alternating) deviates from it — could indicate a farmer-level change worth a
    targeted extension-officer follow-up, not necessarily a problem by itself.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class SeasonRecord:
    season_label: str       # e.g. "Kharif-2024", "Rabi-2024-25"
    crop_type: str


@dataclass
class RotationReport:
    field_id: str
    season_history: list[SeasonRecord]
    flags: list[str]
    same_crop_streak: int
    fallow_seasons_observed: int


def detect_same_crop_streak(history: list[SeasonRecord]) -> int:
    if not history:
        return 0
    streak = 1
    last_crop = history[-1].crop_type
    for record in reversed(history[:-1]):
        if record.crop_type == last_crop:
            streak += 1
        else:
            break
    return streak


def analyze_rotation(field_id: str, history: list[SeasonRecord], streak_alert_threshold: int = 3) -> RotationReport:
    if len(history) < 2:
        logger.info(f"Field {field_id}: insufficient season history ({len(history)}) for rotation analysis")
        return RotationReport(field_id, history, flags=["INSUFFICIENT_HISTORY"], same_crop_streak=len(history), fallow_seasons_observed=0)

    flags: list[str] = []
    streak = detect_same_crop_streak(history)
    fallow_count = sum(1 for r in history if r.crop_type in ("Fallow/Barren", "Fallow"))

    if streak >= streak_alert_threshold:
        flags.append("SAME_CROP_REPEATED")
        logger.warning(f"Field {field_id}: same crop ({history[-1].crop_type}) for {streak} consecutive seasons")

    if fallow_count == 0 and len(history) >= 4:
        flags.append("NO_FALLOW_OBSERVED")

    if len(history) >= 4:
        recent_pattern = [r.crop_type for r in history[-4:-2]]
        latest_pattern = [r.crop_type for r in history[-2:]]
        if recent_pattern and recent_pattern != latest_pattern and streak < streak_alert_threshold:
            # crude rotation-break heuristic: the two-season pattern changed
            flags.append("ROTATION_BREAK")

    if not flags:
        flags.append("NORMAL_ROTATION")

    return RotationReport(
        field_id=field_id, season_history=history, flags=flags,
        same_crop_streak=streak, fallow_seasons_observed=fallow_count,
    )
