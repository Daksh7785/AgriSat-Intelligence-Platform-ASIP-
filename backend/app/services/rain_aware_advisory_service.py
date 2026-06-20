"""
Rain-Aware Advisory Nudge.

Adjusts the raw irrigation advisory (computed from ETc - ETa deficit) against a
short-range rainfall forecast. If meaningful rain is forecast within the advisory's
action window, the recommendation is downgraded or deferred rather than telling a
farmer to irrigate right before rain arrives — a a failure mode that is easy to
introduce if the deficit calculation and the advisory text are not cross-checked
against forecast data, and is exactly the kind of mistake that erodes farmer trust
in the system after a few bad recommendations.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from loguru import logger

RAIN_DEFER_THRESHOLD_MM = 10.0   # forecast rain at/above this offsets the need to irrigate now


@dataclass
class RainAdjustedAdvisory:
    original_advisory_class: str
    original_irrigation_requirement_mm: float
    forecast_rain_mm_next_3_days: float
    adjusted_advisory_class: str
    adjusted_irrigation_requirement_mm: float
    nudge_message: Optional[str]


def apply_rain_nudge(
    advisory_class: str,
    irrigation_requirement_mm: float,
    forecast_rain_mm_next_3_days: float,
) -> RainAdjustedAdvisory:
    adjusted_requirement = max(0.0, irrigation_requirement_mm - forecast_rain_mm_next_3_days)
    nudge_message = None

    severity_order = ["none", "light", "moderate", "critical"]
    original_idx = severity_order.index(advisory_class) if advisory_class in severity_order else 0

    if forecast_rain_mm_next_3_days >= RAIN_DEFER_THRESHOLD_MM and advisory_class != "critical":
        adjusted_class = severity_order[max(0, original_idx - 1)]
        nudge_message = (
            f"Rain of {forecast_rain_mm_next_3_days:.0f}mm expected in the next 3 days — "
            f"consider deferring irrigation to avoid waste."
        )
        logger.info(f"Rain nudge applied: {advisory_class} -> {adjusted_class} "
                    f"(forecast rain={forecast_rain_mm_next_3_days}mm)")
    elif advisory_class == "critical" and forecast_rain_mm_next_3_days >= RAIN_DEFER_THRESHOLD_MM:
        # Severe deficit overrides rain forecast nudging — forecasts can fail, and a
        # severely stressed crop should not wait on a forecast that may not materialize.
        adjusted_class = advisory_class
        nudge_message = (
            f"Rain is forecast ({forecast_rain_mm_next_3_days:.0f}mm) but deficit is "
            f"severe — irrigate now rather than risk relying on an uncertain forecast."
        )
    else:
        adjusted_class = advisory_class

    return RainAdjustedAdvisory(
        original_advisory_class=advisory_class,
        original_irrigation_requirement_mm=irrigation_requirement_mm,
        forecast_rain_mm_next_3_days=forecast_rain_mm_next_3_days,
        adjusted_advisory_class=adjusted_class,
        adjusted_irrigation_requirement_mm=round(adjusted_requirement, 1),
        nudge_message=nudge_message,
    )
