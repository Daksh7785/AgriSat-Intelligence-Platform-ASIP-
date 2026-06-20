"""
Counterfactual Stress Explainer.

Given a field's current and previous-cycle index values (VCI, TCI, VHI, SMI, NDWI,
VH backscatter), generates a deterministic, rule-based natural-language explanation
of what changed and why it was classified at its current stress level. This is
intentionally NOT an LLM call — every explanation must be traceable to a specific
index delta so an ISRO scientist can audit the logic, and it must work with zero
network dependency during a live demo.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from loguru import logger

STRESS_INDEX_LABELS = {
    "vci": "Vegetation Condition Index",
    "tci": "Temperature Condition Index",
    "vhi": "Vegetation Health Index",
    "smi": "Soil Moisture Index (SAR-derived)",
    "ndwi": "NDWI",
    "vh_backscatter": "VH backscatter",
}


@dataclass
class IndexSnapshot:
    vci: float
    tci: float
    vhi: float
    smi: float
    ndwi: float
    vh_backscatter: float
    growth_stage: str


@dataclass
class StressExplanation:
    stress_level: str
    headline: str
    contributing_factors: list[str]
    is_likely_false_alarm: bool
    false_alarm_reason: Optional[str]


# Post-harvest / senescence NDVI drop is the single most common false-positive
# source for naive stress detectors — this is the exact failure mode the design
# doc calls out as a known limitation of competing systems. Gate on growth stage.
FALSE_ALARM_PRONE_STAGES = {"Maturity", "Post-harvest"}


def explain_stress(
    current: IndexSnapshot, previous: Optional[IndexSnapshot], stress_level: str,
) -> StressExplanation:
    factors = []

    if previous is not None:
        vci_delta = current.vci - previous.vci
        smi_delta = current.smi - previous.smi
        vh_delta = current.vh_backscatter - previous.vh_backscatter

        if vci_delta < -0.10:
            factors.append(
                f"VCI dropped {abs(vci_delta)*100:.0f} points over the last cycle "
                f"(vegetation vigor declining relative to its seasonal range)"
            )
        if smi_delta < -0.10:
            factors.append(
                f"SAR-derived soil moisture index fell {abs(smi_delta)*100:.0f} points "
                f"(less moisture in the root zone)"
            )
        if abs(vh_delta) < 0.5 and vci_delta < -0.10:
            factors.append(
                "VH backscatter stayed essentially flat while VCI dropped — "
                "this pattern is consistent with moisture stress, not structural "
                "crop change (a harvest event would show a larger VH shift too)"
            )

    is_false_alarm = False
    false_alarm_reason = None
    if current.growth_stage in FALSE_ALARM_PRONE_STAGES and stress_level != "none" and stress_level != "No Stress":
        is_false_alarm = True
        false_alarm_reason = (
            f"Field is in {current.growth_stage} stage — an NDVI/VCI decline here is "
            f"expected senescence, not water stress. Stage-conditioning should "
            f"normally suppress this alert; flagging for model review if it fired."
        )
        logger.warning(f"Potential false alarm at stage={current.growth_stage}: {false_alarm_reason}")

    if not factors:
        factors.append("No single dominant driver — stress level reflects a sustained "
                        "multi-index pattern rather than one sharp index change.")

    headline = f"{stress_level.capitalize()} stress detected at {current.growth_stage} stage"

    return StressExplanation(
        stress_level=stress_level,
        headline=headline,
        contributing_factors=factors,
        is_likely_false_alarm=is_false_alarm,
        false_alarm_reason=false_alarm_reason,
    )
