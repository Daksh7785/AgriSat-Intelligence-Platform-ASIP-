"""
SHAP-based explainability for the crop classifier.

Explains individual pixel predictions in terms of the 70-dimensional feature vector
(temporal NDVI/EVI/NDWI/LSWI, SAR VV/VH/ratio, texture, phenological summary — see
crop_classifier/model.py for the full feature_names list).

Uses TreeExplainer against the XGBoost component of the voting ensemble (SHAP support
for VotingClassifier/RandomForest is slower and less stable; the XGBoost member is
representative of the ensemble's decision surface and is the standard choice for
tree-based SHAP in production pipelines).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import numpy as np
import shap
from loguru import logger

from app.ml.crop_classifier.model import CropClassifierModel, CROP_CLASSES


@dataclass
class PixelExplanation:
    predicted_class: str
    confidence: float
    top_features: List[dict]   # [{"feature": str, "shap_value": float, "raw_value": float}, ...]
    natural_language_summary: str


class CropClassifierExplainer:
    def __init__(self, model: CropClassifierModel, background_sample: np.ndarray):
        """
        background_sample: a representative subset (e.g. 200-500 rows) of training
        features, used as the SHAP background distribution. Pass a stratified sample
        across crop classes, not a random slice, or rare classes get poor attributions.
        """
        self.model = model
        xgb_estimator = model.model.named_steps["classifier"].estimators_[1]  # xgb member
        scaler = model.model.named_steps["scaler"]
        self._scaled_background = scaler.transform(background_sample)
        self.explainer = shap.TreeExplainer(xgb_estimator)
        logger.info(f"SHAP explainer initialized on {len(background_sample)} background samples")

    def explain_pixel(self, feature_vector: np.ndarray, top_k: int = 5) -> PixelExplanation:
        scaler = self.model.model.named_steps["scaler"]
        x_scaled = scaler.transform(feature_vector.reshape(1, -1))

        pred_class_idx, confidence = self.model.predict(feature_vector.reshape(1, -1))
        pred_class_idx = int(pred_class_idx[0])
        confidence = float(confidence[0])
        predicted_class = CROP_CLASSES[pred_class_idx]

        shap_values = self.explainer.shap_values(x_scaled)
        # Multi-class XGBoost returns a list of arrays (one per class) or a 3D array
        # depending on SHAP version — normalize to the predicted class's contributions.
        if isinstance(shap_values, list):
            class_shap = shap_values[pred_class_idx][0]
        elif isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 2:
                class_shap = shap_values[0]
            elif shap_values.ndim == 3:
                class_shap = shap_values[0, :, pred_class_idx]
            else:
                class_shap = shap_values.flatten()
        else:
            class_shap = np.array(shap_values).flatten()


        feature_names = self.model.feature_names
        order = np.argsort(-np.abs(class_shap))[:top_k]

        top_features = [
            {
                "feature": feature_names[i],
                "shap_value": float(class_shap[i]),
                "raw_value": float(feature_vector[i]),
            }
            for i in order
        ]

        summary = self._build_summary(predicted_class, top_features)

        return PixelExplanation(
            predicted_class=predicted_class,
            confidence=confidence,
            top_features=top_features,
            natural_language_summary=summary,
        )

    def _build_summary(self, predicted_class: str, top_features: List[dict]) -> str:
        """Turns the top SHAP features into one readable sentence for the dashboard."""
        direction_phrases = []
        for f in top_features[:3]:
            direction = "pushed toward" if f["shap_value"] > 0 else "pushed away from"
            direction_phrases.append(f"{f['feature']} ({direction} {predicted_class})")
        return f"Classified as {predicted_class} mainly because of: " + "; ".join(direction_phrases) + "."

    def explain_batch(self, feature_array: np.ndarray, top_k: int = 5) -> List[PixelExplanation]:
        return [self.explain_pixel(row, top_k) for row in feature_array]
