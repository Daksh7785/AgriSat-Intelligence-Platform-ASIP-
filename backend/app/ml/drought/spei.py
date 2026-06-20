"""
SPEI (Standardized Precipitation-Evapotranspiration Index) calculator.

Reference: Vicente-Serrano, Begueria & Lopez-Moreno (2010), "A Multiscalar Drought
Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration
Index." Journal of Climate, 23(7), 1696-1718.

SPEI = standardized water balance (Precipitation - PET) accumulated over a chosen
timescale (commonly 1, 3, 6, 12 months), fit to a log-logistic distribution and
transformed to a standard normal deviate — this makes it comparable across regions
and seasons, unlike raw rainfall deficit.

This implementation uses the log-logistic 3-parameter fit (Vicente-Serrano et al.
2010, Eq. 3-5) rather than the simpler gamma fit used for SPI, since the water
balance series (P - PET) can be negative and the log-logistic handles that domain.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy import stats
from loguru import logger

SPEI_CATEGORIES = [
    (-np.inf, -2.0, "extreme drought"),
    (-2.0, -1.5, "severe drought"),
    (-1.5, -1.0, "moderate drought"),
    (-1.0, 1.0, "normal"),
    (1.0, 1.5, "moderately wet"),
    (1.5, 2.0, "very wet"),
    (2.0, np.inf, "extremely wet"),
]


@dataclass
class SPEIResult:
    spei_values: np.ndarray         # standardized, same length as input series
    category: list[str]
    timescale_months: int


def categorize_spei(value: float) -> str:
    for lo, hi, label in SPEI_CATEGORIES:
        if lo <= value < hi:
            return label
    return "normal"


def compute_water_balance_series(precip_mm: np.ndarray, pet_mm: np.ndarray) -> np.ndarray:
    """D_i = P_i - PET_i, the monthly (or 8-day, if using this at sub-monthly scale) water balance."""
    if precip_mm.shape != pet_mm.shape:
        raise ValueError("Precipitation and PET series must be the same length")
    return precip_mm - pet_mm


def accumulate_timescale(water_balance: np.ndarray, timescale: int) -> np.ndarray:
    """Rolling sum over `timescale` periods (e.g. 3-month SPEI = 3-period rolling sum)."""
    if timescale < 1:
        raise ValueError("timescale must be >= 1")
    kernel = np.ones(timescale)
    accumulated = np.convolve(water_balance, kernel, mode="valid")
    return accumulated


def compute_spei(
    precip_mm: np.ndarray, pet_mm: np.ndarray, timescale_months: int = 3,
) -> SPEIResult:
    water_balance = compute_water_balance_series(precip_mm, pet_mm)
    accumulated = accumulate_timescale(water_balance, timescale_months)

    if len(accumulated) < 10:
        logger.warning(
            f"Only {len(accumulated)} accumulated periods available — SPEI fit is "
            f"unstable with <10 points. Use as an indicative value only."
        )

    # Fit a 3-parameter log-logistic distribution (Fisk distribution in scipy) to the accumulated series.
    # To handle potential fit failures, fall back gracefully to a standard normal scale of water balance z-score
    try:
        shape, loc, scale = stats.fisk.fit(accumulated)
        cdf = stats.fisk.cdf(accumulated, shape, loc, scale)
        cdf = np.clip(cdf, 1e-6, 1 - 1e-6)  # avoid inf at the normal quantile transform
        spei_values = stats.norm.ppf(cdf)
    except Exception as e:
        logger.error(f"Fisk fitting failed: {e}. Falling back to standard normal approximation.")
        mean = np.mean(accumulated)
        std = np.std(accumulated) + 1e-6
        spei_values = (accumulated - mean) / std

    categories = [categorize_spei(float(v)) for v in spei_values]

    logger.info(
        f"SPEI-{timescale_months} computed — latest value={spei_values[-1]:.2f} "
        f"({categories[-1]})"
    )

    return SPEIResult(
        spei_values=spei_values, category=categories, timescale_months=timescale_months,
    )
