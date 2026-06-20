import numpy as np
import pytest
from datetime import date, timedelta
from app.ml.drought.spei import compute_spei
from app.ml.stress_detector.anomaly import compute_pixel_anomaly
from app.ml.stress_detector.lead_time_scorer import score_lead_time


def test_spei_dry_spell():
    # 36 months of precipitation and PET
    np.random.seed(42)
    months = 36
    precip = np.full(months, 80.0)
    pet = np.full(months, 100.0)

    # Inject dry spell in last 6 months
    precip[-6:] = 10.0
    pet[-6:] = 180.0

    res = compute_spei(precip, pet, timescale_months=3)
    assert len(res.spei_values) == months - 3 + 1
    # Check that drought category is triggered at the end of the series
    assert "drought" in res.category[-1]


def test_ndvi_pixel_anomaly():
    # 5 historical years of same period NDVI
    # shape: 5 x 4 x 4
    np.random.seed(0)
    hist_stack = np.random.normal(0.6, 0.05, (5, 4, 4))
    # Standard deviation will be around 0.05

    # Current NDVI: has a drop in the top left pixel (0,0) down to 0.35 (which is 5 std devs below mean)
    current_ndvi = np.full((4, 4), 0.6)
    current_ndvi[0, 0] = 0.3

    res = compute_pixel_anomaly(current_ndvi, hist_stack, min_years_for_pixelwise=3)
    assert res.z_score[0, 0] < -2.0
    assert res.category[0, 0] == "severe_negative_anomaly"
    assert res.category[1, 1] == "normal"


def test_lead_time_evaluation():
    # Create 10 dates at 8-day intervals
    base_date = date(2026, 1, 1)
    dates = [base_date + timedelta(days=8 * i) for i in range(10)]

    # NDVI starts high (0.7) and crashes at step 6 (index 6, date + 48 days) to 0.45
    ndvi = np.array([0.7, 0.7, 0.68, 0.69, 0.7, 0.7, 0.5, 0.48, 0.46, 0.45])

    # Stress detector flags 'moderate' at step 4 (index 4, date + 32 days)
    stress_level = ["none", "none", "none", "mild", "moderate", "severe", "severe", "critical", "critical", "critical"]

    res = score_lead_time(dates, ndvi, stress_level, detector_signal_used="smi")

    # Crash should be detected at step 6 (difference index 5 is 0.7 to 0.5 = -0.2)
    assert res.visible_crash_date == dates[6]  # date at index 6
    assert res.earliest_detector_flag_date == dates[4]  # date at index 4

    # Lead time should be 2 periods (16 days)
    assert res.lead_time_days == 16
