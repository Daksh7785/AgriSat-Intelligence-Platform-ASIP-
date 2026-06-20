"""
Uncertainty quantification for crop classification and stress detection.

Two complementary uncertainty signals, both cheap to compute from outputs the
ensemble already produces:

1. Predictive entropy from the softmax/voting probabilities — high entropy means
   the model is genuinely unsure between classes (e.g. wheat vs mustard look similar
   spectrally in early vegetative stage).
2. Ensemble disagreement — variance between the RF and XGBoost members' individual
   predictions. High disagreement flags pixels where the two model families reach
   different conclusions, which is operationally more actionable than entropy alone
   (it tells you WHICH kind of uncertainty you're looking at).

Pixels in the top quartile of either signal should be flagged for manual review /
prioritized ground-truth collection — this closes the active-learning loop with
Feature 15.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger


@dataclass
class UncertaintyMaps:
    entropy_map: np.ndarray          # H x W, higher = more uncertain
    disagreement_map: np.ndarray     # H x W, higher = RF/XGB disagree more
    review_priority_mask: np.ndarray  # H x W boolean, top-quartile of either signal


def compute_predictive_entropy(probability_array: np.ndarray) -> np.ndarray:
    """probability_array: H x W x n_classes softmax/voting probabilities."""
    eps = 1e-12
    p = np.clip(probability_array, eps, 1.0)
    entropy = -np.sum(p * np.log(p), axis=-1)
    max_entropy = np.log(probability_array.shape[-1])
    return entropy / max_entropy  # normalized to [0, 1]


def compute_ensemble_disagreement(rf_probs: np.ndarray, xgb_probs: np.ndarray) -> np.ndarray:
    """
    rf_probs, xgb_probs: H x W x n_classes probability arrays from each ensemble member.
    Disagreement = 1 - cosine similarity between the two probability vectors per pixel,
    so identical predictions score 0 and maximally divergent predictions score near 1.
    """
    dot = np.sum(rf_probs * xgb_probs, axis=-1)
    norm_rf = np.linalg.norm(rf_probs, axis=-1)
    norm_xgb = np.linalg.norm(xgb_probs, axis=-1)
    cosine_sim = dot / (norm_rf * norm_xgb + 1e-12)
    return 1.0 - np.clip(cosine_sim, -1.0, 1.0)


def build_uncertainty_maps(
    rf_probs: np.ndarray, xgb_probs: np.ndarray, review_quantile: float = 0.75,
) -> UncertaintyMaps:
    combined_probs = (rf_probs + xgb_probs) / 2.0
    entropy_map = compute_predictive_entropy(combined_probs)
    disagreement_map = compute_ensemble_disagreement(rf_probs, xgb_probs)

    entropy_thresh = np.nanquantile(entropy_map, review_quantile)
    disagreement_thresh = np.nanquantile(disagreement_map, review_quantile)
    review_mask = (entropy_map >= entropy_thresh) | (disagreement_map >= disagreement_thresh)

    logger.info(
        f"Uncertainty maps built — {review_mask.sum()} / {review_mask.size} pixels "
        f"({100*review_mask.mean():.1f}%) flagged for review"
    )

    return UncertaintyMaps(
        entropy_map=entropy_map,
        disagreement_map=disagreement_map,
        review_priority_mask=review_mask,
    )
