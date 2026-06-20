"""
Validation & Accuracy Reporting Service.

Generates the accuracy report shown in the demo and stored against model_runs.
Critically: every report carries the ground-truth provenance (real vs synthetic,
see ground_truth_loader.py) so accuracy claims are never presented without context.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, f1_score,
    confusion_matrix, classification_report,
)
from loguru import logger


@dataclass
class AccuracyReport:
    model_version: str
    run_date: str
    overall_accuracy: float
    kappa_coefficient: float
    f1_per_class: dict
    confusion_matrix: list
    n_validation_samples: int
    ground_truth_is_synthetic: bool
    synthetic_fraction: float
    caveat: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ValidationService:
    def __init__(self, db=None):
        self.db = db

    def evaluate_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_names: list[str],
        model_version: str,
        ground_truth_is_synthetic: bool,
        synthetic_fraction: float = 0.0,
    ) -> AccuracyReport:
        oa = float(accuracy_score(y_true, y_pred))
        kappa = float(cohen_kappa_score(y_true, y_pred))
        f1_per_class_arr = f1_score(y_true, y_pred, average=None, labels=list(range(len(class_names))))
        cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))

        caveat = None
        if ground_truth_is_synthetic:
            caveat = (
                f"WARNING: {synthetic_fraction*100:.0f}% of validation labels are "
                f"SYNTHETIC, not field-verified. Report this OA/Kappa as a pipeline "
                f"sanity check, not a real-world accuracy claim, until real ground "
                f"truth is substituted."
            )
            logger.warning(caveat)

        report = AccuracyReport(
            model_version=model_version,
            run_date=datetime.utcnow().isoformat(),
            overall_accuracy=oa,
            kappa_coefficient=kappa,
            f1_per_class={name: float(f1) for name, f1 in zip(class_names, f1_per_class_arr)},
            confusion_matrix=cm.tolist(),
            n_validation_samples=int(len(y_true)),
            ground_truth_is_synthetic=ground_truth_is_synthetic,
            synthetic_fraction=synthetic_fraction,
            caveat=caveat,
        )
        logger.info(
            f"Validation report [{model_version}] — OA={oa:.3f}, Kappa={kappa:.3f}, "
            f"n={len(y_true)}, synthetic={ground_truth_is_synthetic}"
        )
        return report

    def meets_target(self, report: AccuracyReport, min_oa: float = 0.85, min_kappa: float = 0.80) -> bool:
        return report.overall_accuracy >= min_oa and report.kappa_coefficient >= min_kappa

    async def persist(self, report: AccuracyReport, command_area_id: str) -> None:
        if self.db is None:
            logger.warning("No DB session — skipping persistence of validation report")
            return
        await self.db.execute(
            """
            INSERT INTO model_runs
              (id, run_date, command_area_id, model_version, overall_accuracy,
               kappa_coefficient, f1_per_class, status)
            VALUES (gen_random_uuid(), :run_date, :command_area_id, :model_version,
                    :oa, :kappa, :f1_json, :status)
            """,
            {
                "run_date": report.run_date,
                "command_area_id": command_area_id,
                "model_version": report.model_version,
                "oa": report.overall_accuracy,
                "kappa": report.kappa_coefficient,
                "f1_json": report.f1_per_class,
                "status": "synthetic_validation" if report.ground_truth_is_synthetic else "validated",
            },
        )
