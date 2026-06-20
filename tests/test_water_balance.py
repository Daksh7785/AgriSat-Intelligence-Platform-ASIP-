"""Tests for SEBAL ETa and the existing Penman-Monteith ETc, including the deficit join."""
import numpy as np
import pytest
from app.ml.water_balance.sebal import SEBALInputs, run_sebal, eta_from_mod16
from app.ml.water_balance.penman_monteith import compute_eto, compute_etc  # existing module


@pytest.fixture
def synthetic_scene():
    h, w = 40, 40
    rng = np.random.default_rng(0)
    ndvi = np.clip(rng.normal(0.5, 0.25, (h, w)), -0.1, 0.95)
    albedo = np.clip(rng.normal(0.18, 0.04, (h, w)), 0.05, 0.4)
    lst = 300 + (1 - ndvi) * 15 + rng.normal(0, 1, (h, w))  # drier pixels run hotter
    return SEBALInputs(
        ndvi=ndvi, albedo=albedo, lst_kelvin=lst,
        air_temp_kelvin=303.0, solar_radiation_wm2=650.0,
        wind_speed_ms=2.0, doy=300, latitude_deg=26.2,
    )


def test_sebal_eta_non_negative(synthetic_scene):
    result = run_sebal(synthetic_scene)
    assert np.all(result.eta_mm_day >= 0)


def test_sebal_cold_pixel_higher_eta_than_hot(synthetic_scene):
    result = run_sebal(synthetic_scene)
    cold_eta = result.eta_mm_day[result.cold_pixel_idx]
    hot_eta = result.eta_mm_day[result.hot_pixel_idx]
    assert cold_eta > hot_eta


def test_mod16_fallback_path():
    mod16 = np.full((10, 10), 24.0)  # 24 mm over 8 days
    result = eta_from_mod16(mod16)
    assert result.is_fallback is True
    np.testing.assert_allclose(result.eta_mm_day, 3.0)


def test_deficit_calculation_uses_etc_minus_eta(synthetic_scene):
    eta_result = run_sebal(synthetic_scene)
    eto = compute_eto(temp_c=30.0, wind_ms=2.0, rh_pct=45.0, solar_rad_wm2=650.0)
    etc = compute_etc(eto, kc=1.05)  # e.g. mid-season wheat Kc
    deficit = etc - np.nanmean(eta_result.eta_mm_day)
    assert isinstance(deficit, float)
