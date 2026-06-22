"""
Temporal Crop Signature Library — PS-6 Module 1.
Multi-temporal spectral profiles for crop type identification from previous season data.
"""
from __future__ import annotations
import math
import random
from typing import List, Dict, Any

# ── Canonical Spectral Signatures (previous kharif season 2025) ──────────────
# 8-day NDVI/EVI/NDWI composites for each crop type across phenological stages
# Values derived from Sentinel-2 L2A multi-temporal analysis over Punjab

CROP_SIGNATURES: Dict[str, Dict[str, List[float]]] = {
    "wheat": {
        "ndvi":  [0.12, 0.18, 0.32, 0.55, 0.72, 0.80, 0.78, 0.68, 0.52, 0.38, 0.22, 0.14],
        "evi":   [0.09, 0.14, 0.27, 0.47, 0.62, 0.71, 0.69, 0.60, 0.44, 0.31, 0.18, 0.10],
        "ndwi":  [-0.25, -0.18, 0.05, 0.18, 0.30, 0.35, 0.32, 0.20, 0.08, -0.05, -0.18, -0.24],
        "vv_db": [-14.2, -13.8, -12.5, -11.2, -10.5, -11.0, -11.5, -12.0, -13.0, -13.8, -14.5, -15.0],
        "vh_db": [-20.5, -20.0, -18.8, -17.2, -15.8, -15.5, -16.0, -17.0, -18.5, -19.5, -20.5, -21.0],
        "label": "Rabi Wheat (Nov–Apr)",
    },
    "rice": {
        "ndvi":  [0.08, 0.14, 0.30, 0.58, 0.78, 0.82, 0.80, 0.70, 0.50, 0.30, 0.15, 0.08],
        "evi":   [0.06, 0.11, 0.25, 0.50, 0.68, 0.73, 0.71, 0.62, 0.43, 0.24, 0.12, 0.06],
        "ndwi":  [0.40, 0.38, 0.28, 0.15, 0.05, 0.02, 0.04, 0.10, 0.18, 0.30, 0.38, 0.42],
        "vv_db": [-8.5, -9.0, -10.5, -12.0, -11.5, -12.0, -12.5, -11.8, -10.5, -9.5, -8.8, -8.2],
        "vh_db": [-14.5, -15.0, -16.5, -18.0, -17.0, -17.5, -18.0, -17.2, -15.8, -14.8, -14.2, -13.8],
        "label": "Kharif Paddy (Jun–Nov)",
    },
    "cotton": {
        "ndvi":  [0.10, 0.15, 0.28, 0.50, 0.68, 0.72, 0.70, 0.62, 0.48, 0.32, 0.20, 0.12],
        "evi":   [0.08, 0.12, 0.23, 0.43, 0.59, 0.63, 0.61, 0.54, 0.41, 0.26, 0.16, 0.09],
        "ndwi":  [-0.30, -0.22, -0.08, 0.10, 0.22, 0.26, 0.24, 0.16, 0.04, -0.10, -0.22, -0.28],
        "vv_db": [-12.5, -12.0, -11.5, -10.5, -10.0, -10.5, -11.0, -11.8, -12.5, -13.0, -13.5, -14.0],
        "vh_db": [-19.0, -18.5, -17.8, -16.5, -15.8, -16.0, -16.5, -17.5, -18.5, -19.0, -19.5, -20.0],
        "label": "Kharif Cotton (May–Oct)",
    },
    "sugarcane": {
        "ndvi":  [0.18, 0.25, 0.38, 0.55, 0.70, 0.78, 0.80, 0.79, 0.75, 0.68, 0.55, 0.40],
        "evi":   [0.15, 0.21, 0.32, 0.48, 0.62, 0.70, 0.72, 0.71, 0.67, 0.60, 0.48, 0.34],
        "ndwi":  [-0.15, -0.05, 0.08, 0.20, 0.32, 0.40, 0.42, 0.40, 0.36, 0.28, 0.18, 0.05],
        "vv_db": [-13.0, -12.5, -12.0, -11.0, -10.2, -9.8, -9.5, -9.8, -10.5, -11.0, -12.0, -13.0],
        "vh_db": [-19.5, -19.0, -18.0, -16.8, -15.5, -14.8, -14.5, -14.8, -15.8, -16.5, -17.8, -19.0],
        "label": "Perennial Sugarcane (Feb–Jan+1)",
    },
    "fallow": {
        "ndvi":  [0.05, 0.06, 0.07, 0.06, 0.05, 0.04, 0.05, 0.06, 0.07, 0.06, 0.05, 0.05],
        "evi":   [0.03, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.04, 0.04, 0.03, 0.03, 0.03],
        "ndwi":  [-0.40, -0.42, -0.40, -0.42, -0.44, -0.45, -0.44, -0.42, -0.40, -0.42, -0.43, -0.41],
        "vv_db": [-16.0, -16.2, -15.8, -16.0, -16.5, -16.8, -16.5, -16.0, -15.8, -16.2, -16.5, -16.8],
        "vh_db": [-22.0, -22.5, -22.0, -22.2, -22.8, -23.0, -22.8, -22.2, -22.0, -22.5, -22.8, -23.0],
        "label": "Fallow / Bare Soil",
    },
}

# 8-day time step labels
TIME_STEPS = [f"T+{i*8}d" for i in range(12)]
STAGE_LABELS = ["Sowing", "Emergence", "Vegetative-I", "Vegetative-II",
                 "Reproductive", "Flowering", "Grain Fill-I", "Grain Fill-II",
                 "Late Season", "Senescence", "Harvest", "Post-Harvest"]


def get_signature(crop_type: str) -> Dict[str, Any]:
    """Return the canonical spectral signature for a crop type."""
    sig = CROP_SIGNATURES.get(crop_type.lower())
    if not sig:
        return {}
    return {
        "crop_type": crop_type,
        "label": sig["label"],
        "time_steps": TIME_STEPS,
        "stage_labels": STAGE_LABELS,
        "ndvi_profile": sig["ndvi"],
        "evi_profile": sig["evi"],
        "ndwi_profile": sig["ndwi"],
        "vv_profile": sig["vv_db"],
        "vh_profile": sig["vh_db"],
        "peak_ndvi": max(sig["ndvi"]),
        "peak_ndvi_step": sig["ndvi"].index(max(sig["ndvi"])),
        "sos_step": next(i for i, v in enumerate(sig["ndvi"]) if v > 0.20),
        "eos_step": max(i for i, v in enumerate(sig["ndvi"]) if v > 0.20),
    }


def compare_field_to_signature(
    field_ndvi: List[float],
    field_evi: List[float],
    field_ndwi: List[float],
) -> Dict[str, Any]:
    """
    Spectral Angle Mapper (SAM) distance to each crop library signature.
    Returns ranked similarity scores for crop type identification.
    """
    def sam_distance(obs: List[float], ref: List[float]) -> float:
        n = min(len(obs), len(ref))
        dot = sum(obs[i] * ref[i] for i in range(n))
        mag_obs = math.sqrt(sum(x**2 for x in obs[:n]))
        mag_ref = math.sqrt(sum(x**2 for x in ref[:n]))
        if mag_obs == 0 or mag_ref == 0:
            return 1.0
        cos_theta = dot / (mag_obs * mag_ref)
        return math.acos(max(-1.0, min(1.0, cos_theta)))

    scores = {}
    for crop, sig in CROP_SIGNATURES.items():
        sam_ndvi = sam_distance(field_ndvi, sig["ndvi"])
        sam_evi = sam_distance(field_evi, sig["evi"])
        sam_ndwi = sam_distance(field_ndwi, sig["ndwi"])
        # Combined SAM (lower = better match)
        combined_sam = (0.4 * sam_ndvi + 0.35 * sam_evi + 0.25 * sam_ndwi)
        similarity = round(max(0.0, 1.0 - combined_sam / math.pi), 4)
        scores[crop] = similarity

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_crop, best_score = ranked[0]

    return {
        "predicted_crop": best_crop,
        "confidence": best_score,
        "similarity_scores": scores,
        "ranked_matches": [{"crop": c, "similarity": s} for c, s in ranked],
        "method": "Spectral Angle Mapper (SAM) on NDVI+EVI+NDWI temporal profiles",
    }


def get_all_signatures() -> Dict[str, Any]:
    """Return all canonical crop signatures for the Temporal Signature Explorer."""
    return {crop: get_signature(crop) for crop in CROP_SIGNATURES.keys()}
