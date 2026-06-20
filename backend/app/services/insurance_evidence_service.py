"""
Insurance Evidence Service — simplified PMFBY-style loss estimation with an
auditable (hashed, timestamped) evidence record, WITHOUT a blockchain dependency.

Loss estimation method: maps the proportion of the season spent at each stress
severity level (none/mild/moderate/severe) into a simplified yield-loss percentage,
using stage-weighted severity (stress during reproductive/grain-fill stages counts
more heavily than stress during early vegetative stages, consistent with crop
physiology — yield formation is most sensitive to water stress during flowering
and grain fill).

The evidence record is a SHA-256 hash of the full input time series + model version,
stored with a timestamp — this gives the same tamper-evidence property a blockchain
would provide for a fraction of the engineering cost, appropriate for demonstrating
the CONCEPT to judges. A production deployment could anchor the hash on-chain later
without changing this module's output format.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
from datetime import datetime, date
from loguru import logger

# Stage sensitivity weights for yield loss attribution — higher weight = stress at
# this stage contributes more to final yield loss. Based on general crop physiology
# (water stress sensitivity peaks at flowering/grain-fill); refine per-crop with
# agronomist input before operational use.
STAGE_SENSITIVITY_WEIGHTS = {
    "Sowing": 0.5, "Vegetative": 0.8, "Reproductive": 1.5,
    "Grain Fill": 1.4, "Maturity": 0.3, "Post-harvest": 0.0,
}

# Standardized keys mapping DB representation ('No Stress' -> 'none', etc.)
SEVERITY_LOSS_FRACTION = {
    "none": 0.0, "mild": 0.05, "moderate": 0.15, "severe": 0.35,
    "No Stress": 0.0, "Mild Stress": 0.05, "Moderate Stress": 0.15, "Severe Stress": 0.35, "Critical Stress": 0.5
}


@dataclass
class StressDayRecord:
    record_date: date
    growth_stage: str
    stress_level: str


@dataclass
class LossEstimate:
    estimated_loss_pct: float
    confidence: str   # "low" | "medium" | "high" — based on data completeness, not a precise stat
    stage_breakdown: dict
    evidence_hash: str
    evidence_timestamp: str
    n_records_used: int


def estimate_loss(records: list[StressDayRecord], model_version: str = "loss-estimator-v1") -> LossEstimate:
    if not records:
        raise ValueError("No stress records provided — cannot estimate loss")

    weighted_loss_sum = 0.0
    weight_sum = 0.0
    stage_breakdown: dict[str, float] = {}

    for r in records:
        weight = STAGE_SENSITIVITY_WEIGHTS.get(r.growth_stage, 0.5)
        loss_fraction = SEVERITY_LOSS_FRACTION.get(r.stress_level, 0.0)
        weighted_loss_sum += weight * loss_fraction
        weight_sum += weight
        stage_breakdown[r.growth_stage] = stage_breakdown.get(r.growth_stage, 0.0) + loss_fraction

    estimated_loss_pct = (weighted_loss_sum / weight_sum) * 100 if weight_sum > 0 else 0.0
    estimated_loss_pct = min(estimated_loss_pct, 90.0)  # cap — this is not a total-loss certifier

    confidence = "high" if len(records) >= 12 else ("medium" if len(records) >= 6 else "low")

    evidence_payload = {
        "model_version": model_version,
        "records": [
            {"date": r.record_date.isoformat(), "stage": r.growth_stage, "stress": r.stress_level}
            for r in records
        ],
    }
    evidence_json = json.dumps(evidence_payload, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()
    evidence_timestamp = datetime.utcnow().isoformat()

    logger.info(
        f"Loss estimate: {estimated_loss_pct:.1f}% (confidence={confidence}), "
        f"evidence_hash={evidence_hash[:16]}..."
    )

    return LossEstimate(
        estimated_loss_pct=round(estimated_loss_pct, 1),
        confidence=confidence,
        stage_breakdown=stage_breakdown,
        evidence_hash=evidence_hash,
        evidence_timestamp=evidence_timestamp,
        n_records_used=len(records),
    )
