import numpy as np
import pytest
from app.ml.zonation.subfield_zones import zone_field
from app.ml.zonation.boundary_refinement import compute_boundary_discrepancy
from app.services.rotation_tracker_service import SeasonRecord, analyze_rotation


def test_kmeans_zonation():
    # Create a 10x10 field mask representing a field
    field_mask = np.ones((10, 10), dtype=bool)

    # Let's create a clear two-zone pattern: left half low, right half high
    np.random.seed(42)
    vci = np.zeros((10, 10))
    vci[:, :5] = np.random.normal(0.2, 0.05, (10, 5))
    vci[:, 5:] = np.random.normal(0.8, 0.05, (10, 5))

    smi = np.zeros((10, 10))
    smi[:, :5] = np.random.normal(0.2, 0.05, (10, 5))
    smi[:, 5:] = np.random.normal(0.7, 0.05, (10, 5))

    ndwi = np.zeros((10, 10))
    ndwi[:, :5] = np.random.normal(0.1, 0.05, (10, 5))
    ndwi[:, 5:] = np.random.normal(0.45, 0.05, (10, 5))

    res = zone_field(field_mask, vci, smi, ndwi)
    assert res.n_zones == 2
    # Verify that the two zones have distinctly separated VCI means
    assert abs(res.zone_summary[0]["mean_vci"] - res.zone_summary[1]["mean_vci"]) > 0.4
    assert res.silhouette_score > 0.5


def test_boundary_refinement():
    # 20x20 command area
    official_boundary = np.zeros((20, 20), dtype=bool)
    official_boundary[2:18, 2:18] = True  # a box in the middle

    # Let's create a VH backscatter array where there's a 15% discrepancy
    # wetness_thresh = -14.0, lower means ponded/irrigated
    vh = np.full((20, 20), -12.0)  # dry everywhere except...
    # irrigated zone matches official but extends outside by a strip
    vh[2:18, 2:18] = -16.0
    vh[2:18, 18:20] = -16.0  # extra strip irrigated outside the boundary

    res = compute_boundary_discrepancy(official_boundary, vh)
    assert res.outside_boundary_but_irrigated_pct > 10.0
    assert bool(res.flagged_for_review) is True
    # check that map has value 2 (outside but irrigated)
    assert np.any(res.discrepancy_map == 2)


def test_rotation_tracker_flags():
    # 1. 4 consecutive Cotton crops -> SAME_CROP_REPEATED, NO_FALLOW_OBSERVED
    cotton_streak = [
        SeasonRecord("Kharif-2023", "Cotton"),
        SeasonRecord("Rabi-2023-24", "Cotton"),
        SeasonRecord("Kharif-2024", "Cotton"),
        SeasonRecord("Rabi-2024-25", "Cotton"),
    ]
    res1 = analyze_rotation("field_1", cotton_streak)
    assert "SAME_CROP_REPEATED" in res1.flags
    assert "NO_FALLOW_OBSERVED" in res1.flags
    assert res1.same_crop_streak == 4

    # 2. Alternating Rice and Fallow -> NORMAL_ROTATION
    alternating = [
        SeasonRecord("Kharif-2023", "Rice/Paddy"),
        SeasonRecord("Rabi-2023-24", "Fallow"),
        SeasonRecord("Kharif-2024", "Rice/Paddy"),
        SeasonRecord("Rabi-2024-25", "Fallow"),
    ]
    res2 = analyze_rotation("field_2", alternating)
    assert "NORMAL_ROTATION" in res2.flags
    assert res2.same_crop_streak == 1


