import numpy as np
import pytest
from app.ml.crop_classifier.explainability import CropClassifierExplainer
from app.ml.crop_classifier.model import CropClassifierModel
from app.ml.crop_classifier.uncertainty import (
    compute_predictive_entropy,
    compute_ensemble_disagreement,
    build_uncertainty_maps,
)
from app.services.stress_explainer_service import IndexSnapshot, explain_stress


def test_shap_explanation():
    # Construct a CropClassifierModel and fit on some synthetic data
    n_features = 70
    model = CropClassifierModel(n_estimators_rf=2, n_estimators_xgb=2)
    model.build_feature_names()

    np.random.seed(42)
    dummy_X = np.random.uniform(0.1, 0.9, (10, n_features))
    dummy_y = np.array([0, 1] * 5)
    model.train(dummy_X, dummy_y)

    background_sample = np.random.uniform(0.1, 0.9, (5, n_features))
    explainer = CropClassifierExplainer(model, background_sample)

    pixel_feats = np.random.uniform(0.1, 0.9, n_features)
    explanation = explainer.explain_pixel(pixel_feats, top_k=3)

    assert explanation.predicted_class in ["Wheat", "Rice/Paddy"]
    assert len(explanation.top_features) == 3
    assert "shap_value" in explanation.top_features[0]
    assert explanation.natural_language_summary.startswith("Classified as")


def test_uncertainty_math():
    # 1. Identical probabilities -> disagreement should be 0
    probs_rf = np.array([[[1.0, 0.0], [0.5, 0.5]]])
    probs_xgb = np.array([[[1.0, 0.0], [0.5, 0.5]]])

    disagreement = compute_ensemble_disagreement(probs_rf, probs_xgb)
    assert np.allclose(disagreement, 0.0, atol=1e-5)

    # 2. Opposite probabilities -> disagreement should approach 1.0 (cosine sim = 0)
    # Cosine similarity between [1.0, 0.0] and [0.0, 1.0] is 0 -> disagreement 1 - 0 = 1.0
    p1 = np.array([[[1.0, 0.0]]])
    p2 = np.array([[[0.0, 1.0]]])
    disagreement_opp = compute_ensemble_disagreement(p1, p2)
    assert np.allclose(disagreement_opp, 1.0, atol=1e-5)

    # 3. Entropy math: uniform distribution should yield maximum normalized entropy (1.0)
    p_uniform = np.array([[[0.2, 0.2, 0.2, 0.2, 0.2]]])
    entropy = compute_predictive_entropy(p_uniform)
    assert np.allclose(entropy, 1.0, atol=1e-5)

    # Peak distribution should yield near 0 entropy
    p_peak = np.array([[[0.9999, 0.0001 / 4, 0.0001 / 4, 0.0001 / 4, 0.0001 / 4]]])
    entropy_peak = compute_predictive_entropy(p_peak)
    assert np.allclose(entropy_peak, 0.0, atol=1e-2)


def test_stress_explanation_false_alarm():
    # Case 1: Vegetation stage VCI drop -> not a false alarm
    current_veg = IndexSnapshot(vci=0.25, tci=0.4, vhi=0.3, smi=0.2, ndwi=0.1, vh_backscatter=-15.5, growth_stage="Vegetative")
    previous_veg = IndexSnapshot(vci=0.45, tci=0.4, vhi=0.4, smi=0.35, ndwi=0.25, vh_backscatter=-15.3, growth_stage="Vegetative")

    expl_veg = explain_stress(current_veg, previous_veg, "moderate")
    assert expl_veg.is_likely_false_alarm is False
    assert len(expl_veg.contributing_factors) > 0

    # Case 2: Maturity stage VCI drop -> likely a false alarm (senescence)
    current_mat = IndexSnapshot(vci=0.25, tci=0.4, vhi=0.3, smi=0.2, ndwi=0.1, vh_backscatter=-15.5, growth_stage="Maturity")
    previous_mat = IndexSnapshot(vci=0.45, tci=0.4, vhi=0.4, smi=0.35, ndwi=0.25, vh_backscatter=-15.3, growth_stage="Maturity")

    expl_mat = explain_stress(current_mat, previous_mat, "moderate")
    assert expl_mat.is_likely_false_alarm is True
    assert expl_mat.false_alarm_reason is not None
