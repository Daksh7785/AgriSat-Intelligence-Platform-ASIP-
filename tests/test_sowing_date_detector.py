"""Tests for sowing date detection, including the disagreement-handling path."""
from datetime import date, timedelta
import numpy as np
from app.utils.sowing_date_detector import detect_sowing_date


def _dates(n, start=date(2025, 6, 1), step_days=8):
    return [start + timedelta(days=step_days * i) for i in range(n)]


def test_optical_only_detects_rise():
    dates = _dates(10)
    ndvi = np.array([0.2, 0.22, 0.21, 0.45, 0.55, 0.6, 0.65, 0.68, 0.7, 0.7])
    result = detect_sowing_date(dates, ndvi)
    assert result.sowing_date is not None
    assert result.method == "optical"


def test_agreement_between_optical_and_sar():
    dates = _dates(10)
    ndvi = np.array([0.2, 0.22, 0.21, 0.45, 0.55, 0.6, 0.65, 0.68, 0.7, 0.7])
    vv = np.array([-7, -7.2, -10, -10.5, -10.6, -10.4, -10.5, -10.5, -10.5, -10.5])
    result = detect_sowing_date(dates, ndvi, vv)
    assert result.method in ("optical+sar_agree", "optical")
    assert result.confidence >= 0.7


def test_disagreement_defaults_to_optical():
    dates = _dates(12)
    ndvi = np.array([0.2]*5 + [0.5, 0.6, 0.65, 0.68, 0.7, 0.7, 0.7])
    vv = np.array([-7, -7, -7, -7, -7, -7, -7, -7, -7, -10.5, -10.5, -10.5])
    result = detect_sowing_date(dates, ndvi, vv, max_disagreement_composites=1)
    assert result.method == "disagreement_optical_default"
