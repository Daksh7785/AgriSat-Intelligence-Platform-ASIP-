import numpy as np
import pytest
from datetime import date
from app.ml.yield_forecast.model import YieldForecastModel, POTENTIAL_YIELD_KG_HA
from app.services.roi_calculator_service import compute_cycle_savings, aggregate_seasonal_savings
from app.services.insurance_evidence_service import estimate_loss, StressDayRecord


def test_yield_model_regression():
    # Generate clean synthetic data where yield = 200 * ndvi + 0.5 * gdd
    np.random.seed(42)
    n_samples = 50
    ndvi_int = np.random.uniform(8.0, 16.0, n_samples)
    gdd_acc = np.random.uniform(1500.0, 2500.0, n_samples)
    yield_obs = ndvi_int * 200.0 + gdd_acc * 0.5 + np.random.normal(0, 10.0, n_samples)

    model = YieldForecastModel()
    metrics = model.train(ndvi_int, gdd_acc, yield_obs)

    # R2 should be very high due to low noise
    assert metrics["r2"] > 0.95
    assert metrics["mae_kg_ha"] < 30.0

    # Predict for a typical wheat pixel
    forecast = model.predict(12.0, 2000.0, "Wheat")
    # Expected yield around 12*200 + 2000*0.5 = 3400
    assert 3200 <= forecast.predicted_yield_kg_ha <= 3600
    assert forecast.pct_of_potential == round((forecast.predicted_yield_kg_ha / POTENTIAL_YIELD_KG_HA["Wheat"]) * 100, 1)
    assert forecast.risk_category in ["on_track", "moderate_risk"]


def test_roi_savings_math():
    # 20mm recommended irrigation on 1.0 hectare
    # Baseline over-irrigation = 35% -> baseline_flood = 27.0mm -> saved = 7.0mm
    # 1mm over 1ha = 10,000 liters -> saved = 70,000 liters
    res = compute_cycle_savings(irrigation_requirement_mm=20.0, field_area_hectares=1.0)
    assert res.baseline_flood_irrigation_mm == 27.0
    assert res.water_saved_liters == 70000.0
    # Cost = 70m3 * 1.8 Rs/m3 = 126.0 Rs
    assert res.cost_saved_rs == 126.0

    # Aggregate check
    agg = aggregate_seasonal_savings([res, res])
    assert agg["n_cycles"] == 2
    assert agg["total_water_saved_liters"] == 140000.0
    assert agg["total_cost_saved_rs"] == 252.0


def test_insurance_stage_weighting():
    # Case 1: severe stress in reproductive and grain fill stages, normal elsewhere
    records_critical = [
        StressDayRecord(record_date=date(2026, 1, 1), growth_stage="Sowing", stress_level="none"),
        StressDayRecord(record_date=date(2026, 1, 9), growth_stage="Vegetative", stress_level="none"),
        StressDayRecord(record_date=date(2026, 1, 17), growth_stage="Reproductive", stress_level="severe"),
        StressDayRecord(record_date=date(2026, 1, 25), growth_stage="Grain Fill", stress_level="severe"),
        StressDayRecord(record_date=date(2026, 2, 2), growth_stage="Maturity", stress_level="none"),
    ]
    loss_critical = estimate_loss(records_critical)

    # Case 2: same severe stress but in sowing and maturity stages, normal elsewhere
    records_low_weight = [
        StressDayRecord(record_date=date(2026, 1, 1), growth_stage="Sowing", stress_level="severe"),
        StressDayRecord(record_date=date(2026, 1, 9), growth_stage="Vegetative", stress_level="none"),
        StressDayRecord(record_date=date(2026, 1, 17), growth_stage="Reproductive", stress_level="none"),
        StressDayRecord(record_date=date(2026, 1, 25), growth_stage="Grain Fill", stress_level="none"),
        StressDayRecord(record_date=date(2026, 2, 2), growth_stage="Maturity", stress_level="severe"),
    ]
    loss_low_weight = estimate_loss(records_low_weight)

    # Critical stage loss should be significantly higher
    assert loss_critical.estimated_loss_pct > loss_low_weight.estimated_loss_pct
    assert loss_critical.evidence_hash is not None
    assert len(loss_critical.evidence_hash) == 64

