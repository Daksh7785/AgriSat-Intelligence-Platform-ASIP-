"""
Sub-Field Management Zonation.

Clusters pixels WITHIN a single field's boundary into 2-4 management zones based on
the existing stress feature stack (VCI, SMI, NDWI, VH backscatter), so an irrigation
advisory can say "irrigate the north-west third of this field" instead of treating
the whole field as one unit. This is standard precision-agriculture practice
(management zone delineation) applied at the satellite-pixel scale rather than
requiring a soil sensor grid.

Method: K-means on standardized per-pixel features within the field mask, with K
selected automatically via silhouette score (capped at 4 zones — more than that is
not actionable for a smallholder field at 10m resolution).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from loguru import logger


@dataclass
class ZonationResult:
    zone_map: np.ndarray          # same shape as field mask, int zone id or -1 outside field
    n_zones: int
    zone_summary: list[dict]      # mean VCI/SMI/NDWI per zone, ranked worst-to-best
    silhouette_score: float


def _select_k(features_scaled: np.ndarray, k_range: range = range(2, 5)) -> int:
    best_k, best_score = 2, -1.0
    for k in k_range:
        if len(features_scaled) <= k:
            continue
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(features_scaled)
        score = silhouette_score(features_scaled, labels)
        if score > best_score:
            best_k, best_score = k, score
    return best_k


def zone_field(
    field_mask: np.ndarray,           # H x W boolean, True inside the field boundary
    vci: np.ndarray, smi: np.ndarray, ndwi: np.ndarray,
) -> ZonationResult:
    if field_mask.sum() < 8:
        raise ValueError("Field too small in pixels for sub-field zonation (need >= 8 pixels)")

    rows, cols = np.where(field_mask)
    feature_stack = np.column_stack([vci[rows, cols], smi[rows, cols], ndwi[rows, cols]])
    feature_stack = np.nan_to_num(feature_stack, nan=np.nanmean(feature_stack))

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(feature_stack)

    k = _select_k(features_scaled)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)
    sil_score = silhouette_score(features_scaled, labels)

    zone_map = np.full(field_mask.shape, -1, dtype=np.int8)
    zone_map[rows, cols] = labels

    zone_summary = []
    for zone_id in range(k):
        zone_pixels = labels == zone_id
        zone_summary.append({
            "zone_id": int(zone_id),
            "n_pixels": int(zone_pixels.sum()),
            "mean_vci": float(np.mean(feature_stack[zone_pixels, 0])),
            "mean_smi": float(np.mean(feature_stack[zone_pixels, 1])),
            "mean_ndwi": float(np.mean(feature_stack[zone_pixels, 2])),
        })
    zone_summary.sort(key=lambda z: z["mean_vci"])  # worst (lowest VCI) first

    logger.info(f"Sub-field zonation: {k} zones, silhouette={sil_score:.3f}")

    return ZonationResult(
        zone_map=zone_map, n_zones=k, zone_summary=zone_summary, silhouette_score=float(sil_score),
    )
