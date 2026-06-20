"""
Vegetation and Soil Moisture Stress Indices calculation.
"""
from __future__ import annotations
import numpy as np


def compute_ndvi(nir: np.ndarray, red: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red)"""
    return (nir - red) / (nir + red + epsilon)


def compute_ndwi(nir: np.ndarray, swir: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """NDWI = (NIR - SWIR) / (NIR + SWIR)"""
    return (nir - swir) / (nir + swir + epsilon)


def compute_vci(ndvi: np.ndarray, ndvi_min: float, ndvi_max: float, epsilon: float = 1e-6) -> np.ndarray:
    """VCI = 100 * (NDVI - NDVI_min) / (NDVI_max - NDVI_min)"""
    return 100.0 * (ndvi - ndvi_min) / (ndvi_max - ndvi_min + epsilon)


def compute_tci(lst: np.ndarray, lst_min: float, lst_max: float, epsilon: float = 1e-6) -> np.ndarray:
    """TCI = 100 * (LST_max - LST) / (LST_max - LST_min)"""
    return 100.0 * (lst_max - lst) / (lst_max - lst_min + epsilon)


def compute_vhi(vci: np.ndarray, tci: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """VHI = alpha * VCI + (1 - alpha) * TCI"""
    return alpha * vci + (1.0 - alpha) * tci


def compute_smi(vh_vv_ratio: np.ndarray, ratio_min: float, ratio_max: float, epsilon: float = 1e-6) -> np.ndarray:
    """SMI = (VH/VV - ratio_min) / (ratio_max - ratio_min)"""
    return (vh_vv_ratio - ratio_min) / (ratio_max - ratio_min + epsilon)
