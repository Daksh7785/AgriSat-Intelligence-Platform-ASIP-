import numpy as np
import pytest
from datetime import date
from app.data.cloud_triage_logger import decide, summarize_season
from app.ml.fusion.multisat_reconciliation import SensorScene, reconcile_scenes


def test_cloud_triage_decisions():
    command_area = "CHAMBAL_MP"
    today = date(2026, 6, 20)

    # Case 1: Low cloud cover -> OPTICAL_PRIMARY
    d1 = decide(today, command_area, cloud_cover_pct=5.0, sar_available=True)
    assert d1.decision == "OPTICAL_PRIMARY"

    # Case 2: Heavy cloud cover with SAR -> SAR_FALLBACK
    d2 = decide(today, command_area, cloud_cover_pct=85.0, sar_available=True)
    assert d2.decision == "SAR_FALLBACK"

    # Case 3: Heavy cloud cover without SAR -> SKIPPED_NO_USABLE_DATA
    d3 = decide(today, command_area, cloud_cover_pct=85.0, sar_available=False)
    assert d3.decision == "SKIPPED_NO_USABLE_DATA"

    # Case 4: Partial cloud cover with SAR -> OPTICAL_SAR_BLEND
    d4 = decide(today, command_area, cloud_cover_pct=25.0, sar_available=True)
    assert d4.decision == "OPTICAL_SAR_BLEND"

    # Case 5: Partial cloud cover without SAR -> OPTICAL_PRIMARY (fallback)
    d5 = decide(today, command_area, cloud_cover_pct=25.0, sar_available=False)
    assert d5.decision == "OPTICAL_PRIMARY"

    # Season summary check
    summary = summarize_season([d1, d2, d3, d4, d5])
    assert summary["total_acquisitions"] == 5
    assert summary["data_gaps"] == 1
    assert summary["pct_sar_fallback_or_blend"] == 40.0


def test_multi_satellite_reconciliation():
    # 2x2 pixels
    # Sentinel-2: NDVI=0.6, cloud cover=10% (clear fraction=0.9), reliability=1.0 -> weight = 0.9
    # AWiFS: NDVI=0.5, cloud cover=50% (clear fraction=0.5), reliability=0.85 -> weight = 0.425
    s2 = SensorScene(
        sensor="Sentinel-2",
        index_value=np.full((2, 2), 0.6),
        cloud_fraction=np.full((2, 2), 0.1)
    )
    awifs = SensorScene(
        sensor="AWiFS",
        index_value=np.full((2, 2), 0.5),
        cloud_fraction=np.full((2, 2), 0.5)
    )

    res = reconcile_scenes([s2, awifs])
    # The blended value should be closer to Sentinel-2 (0.6) than AWiFS (0.5)
    # Blended = (0.9 * 0.6 + 0.425 * 0.5) / (0.9 + 0.425) = (0.54 + 0.2125) / 1.325 = 0.7525 / 1.325 = 0.5679
    expected = (0.9 * 0.6 + 0.425 * 0.5) / (0.9 + 0.425)
    np.testing.assert_allclose(res.blended_value, expected, atol=1e-5)
    assert res.sensors_used == ["Sentinel-2", "AWiFS"]
    assert np.all(res.n_sensors_contributing == 2)
