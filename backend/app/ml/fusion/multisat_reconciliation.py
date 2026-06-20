"""
Multi-Satellite Reconciliation Layer.

When more than one optical sensor (Sentinel-2, AWiFS/LISS-III, Landsat) has a
partial-cloud scene covering the same pixel within the same compositing window,
blend their NDVI (or other index) values using inverse-cloud-fraction weighting
rather than picking a single "best" scene and discarding the rest.

weight_i = (1 - cloud_fraction_i) * sensor_reliability_i
blended_value = sum(weight_i * value_i) / sum(weight_i)

sensor_reliability is a documented, configurable per-sensor multiplier (not a
fitted parameter) reflecting known relative strengths — e.g. Sentinel-2's atmospheric
correction is generally more mature than AWiFS's for this use case, so it carries
a slightly higher base reliability — adjust per validated regional experience.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger

SENSOR_RELIABILITY = {
    "Sentinel-2": 1.0, "Landsat": 0.95, "AWiFS": 0.85, "LISS-III": 0.9, "MODIS": 0.7,
}


@dataclass
class SensorScene:
    sensor: str
    index_value: np.ndarray      # H x W, e.g. NDVI
    cloud_fraction: np.ndarray   # H x W, 0-1, per-pixel cloud probability


@dataclass
class ReconciliationResult:
    blended_value: np.ndarray
    n_sensors_contributing: np.ndarray   # H x W, how many sensors had usable data per pixel
    sensors_used: list[str]


def reconcile_scenes(
    scenes: list[SensorScene], min_clear_fraction: float = 0.3,
) -> ReconciliationResult:
    if not scenes:
        raise ValueError("No scenes provided for reconciliation")

    shape = scenes[0].index_value.shape
    weighted_sum = np.zeros(shape)
    weight_sum = np.zeros(shape)
    contributing_count = np.zeros(shape, dtype=np.int8)

    for scene in scenes:
        reliability = SENSOR_RELIABILITY.get(scene.sensor, 0.75)
        clear_fraction = 1.0 - scene.cloud_fraction
        usable = clear_fraction >= min_clear_fraction
        weight = np.where(usable, clear_fraction * reliability, 0.0)

        weighted_sum += weight * np.nan_to_num(scene.index_value, nan=0.0)
        weight_sum += weight
        contributing_count += usable.astype(np.int8)

    blended = np.divide(weighted_sum, weight_sum, out=np.full(shape, np.nan), where=weight_sum > 0)

    n_no_data = np.sum(weight_sum == 0)
    logger.info(
        f"Multi-sensor reconciliation: {len(scenes)} scenes blended, "
        f"{n_no_data} pixels with no usable data from any sensor "
        f"({100*n_no_data/blended.size:.1f}%)"
    )

    return ReconciliationResult(
        blended_value=blended,
        n_sensors_contributing=contributing_count,
        sensors_used=[s.sensor for s in scenes],
    )
