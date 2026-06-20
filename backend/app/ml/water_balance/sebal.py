"""
SEBAL (Surface Energy Balance Algorithm for Land) — simplified implementation
for estimating actual evapotranspiration (ETa) from optical + thermal bands.

Reference: Bastiaanssen et al. (1998), "A remote sensing surface energy balance
algorithm for land (SEBAL): 1. Formulation." Journal of Hydrology, 212-213, 198-212.

This is the SIMPLIFIED single-pass variant suitable for a hackathon timeline:
  - Anchor pixels (hot/cold) selected by NDVI + surface temperature percentiles
    rather than manual selection.
  - Net radiation (Rn) from broadband albedo + surface/air temperature.
  - Soil heat flux (G) from an empirical NDVI/albedo/Rn relation.
  - Sensible heat flux (H) via Monin-Obukhov iteration is APPROXIMATED with a
    single-step calibration between hot and cold pixels (no full iterative
    stability correction) — documented limitation, acceptable for a 30-hour
    prototype, not for an operational system.

Falls back to MOD16A2 (MODIS ET product) ingestion when thermal bands (Landsat/
Sentinel-3 LST) are unavailable for the requested date — see `eta_from_mod16()`.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
from loguru import logger

STEFAN_BOLTZMANN = 5.67e-8       # W/m^2/K^4
SOLAR_CONSTANT = 1367.0          # W/m^2
LATENT_HEAT_VAPORIZATION = 2.45e6  # J/kg


@dataclass
class SEBALInputs:
    ndvi: np.ndarray             # H x W
    albedo: np.ndarray           # H x W, broadband surface albedo [0,1]
    lst_kelvin: np.ndarray       # H x W, land surface temperature
    air_temp_kelvin: float       # scalar, near-surface air temp at acquisition time
    solar_radiation_wm2: float   # incoming shortwave radiation at acquisition
    wind_speed_ms: float
    doy: int                     # day of year, for solar geometry
    latitude_deg: float


@dataclass
class SEBALResult:
    eta_mm_day: np.ndarray       # H x W, daily actual ET in mm
    net_radiation_wm2: np.ndarray
    soil_heat_flux_wm2: np.ndarray
    sensible_heat_flux_wm2: np.ndarray
    hot_pixel_idx: tuple
    cold_pixel_idx: tuple
    is_fallback: bool = False


def select_anchor_pixels(ndvi: np.ndarray, lst: np.ndarray) -> tuple[tuple, tuple]:
    """
    Automated hot/cold anchor pixel selection.
    Cold pixel: high NDVI (>90th pct), low LST (<10th pct among high-NDVI pixels)
                — represents a well-watered, fully-transpiring reference.
    Hot pixel: low NDVI (<10th pct, bare soil/fallow), high LST (>90th pct)
                — represents a dry, non-transpiring reference.
    """
    valid = ~np.isnan(ndvi) & ~np.isnan(lst)
    ndvi_v, lst_v = ndvi[valid], lst[valid]

    ndvi_hi_thresh = np.nanpercentile(ndvi_v, 90)
    ndvi_lo_thresh = np.nanpercentile(ndvi_v, 10)

    cold_candidates = (ndvi >= ndvi_hi_thresh) & valid
    hot_candidates = (ndvi <= ndvi_lo_thresh) & valid

    if not cold_candidates.any() or not hot_candidates.any():
        raise ValueError("Could not isolate hot/cold anchor pixels — check input rasters")

    cold_lst_vals = np.where(cold_candidates, lst, np.nan)
    hot_lst_vals = np.where(hot_candidates, lst, np.nan)

    cold_idx = np.unravel_index(np.nanargmin(cold_lst_vals), lst.shape)
    hot_idx = np.unravel_index(np.nanargmax(hot_lst_vals), lst.shape)

    logger.info(f"SEBAL anchors — cold pixel: {cold_idx} (LST={lst[cold_idx]:.1f}K), "
                f"hot pixel: {hot_idx} (LST={lst[hot_idx]:.1f}K)")
    return hot_idx, cold_idx


def compute_net_radiation(inputs: SEBALInputs) -> np.ndarray:
    """Rn = (1-albedo)*Rs_in + Rl_in - Rl_out - (1-emissivity)*Rl_in"""
    emissivity = 0.95 + 0.01 * np.clip(inputs.ndvi, 0, 1)  # crude NDVI-emissivity relation
    rl_out = emissivity * STEFAN_BOLTZMANN * inputs.lst_kelvin ** 4
    rl_in = STEFAN_BOLTZMANN * (inputs.air_temp_kelvin ** 4) * 0.85  # simplified atm emissivity
    rn = (1 - inputs.albedo) * inputs.solar_radiation_wm2 + rl_in - rl_out
    return np.clip(rn, 0, None)


def compute_soil_heat_flux(ndvi: np.ndarray, albedo: np.ndarray,
                            lst_kelvin: np.ndarray, rn: np.ndarray) -> np.ndarray:
    """Empirical Bastiaanssen (1998) G/Rn ratio as a function of albedo, LST, NDVI."""
    g_ratio = (lst_kelvin - 273.15) / albedo * (0.0038 * albedo + 0.0074 * albedo ** 2) \
        * (1 - 0.98 * ndvi ** 4)
    g_ratio = np.clip(g_ratio, 0.05, 0.5)
    return g_ratio * rn


def compute_sensible_heat_flux(
    rn: np.ndarray, g: np.ndarray, lst_kelvin: np.ndarray,
    hot_idx: tuple, cold_idx: tuple,
) -> np.ndarray:
    """
    Single-step calibrated H using the hot/cold pixel pair:
    at the cold pixel, H ≈ 0 (all energy goes to ET).
    at the hot pixel, H ≈ Rn - G (no available water, all energy goes to sensible heat).
    A linear dT-to-H relationship is fit between the two anchors and applied to the scene.
    """
    h_cold = 0.0
    h_hot = float(rn[hot_idx] - g[hot_idx])
    dt_cold = 0.0
    dt_hot = float(lst_kelvin[hot_idx] - lst_kelvin[cold_idx])

    if dt_hot <= 0:
        raise ValueError("Hot pixel LST must exceed cold pixel LST — check anchor selection")

    slope = (h_hot - h_cold) / dt_hot
    dt_scene = lst_kelvin - lst_kelvin[cold_idx]
    h = h_cold + slope * dt_scene
    return np.clip(h, 0, rn)  # H cannot exceed available energy


def run_sebal(inputs: SEBALInputs) -> SEBALResult:
    """Full simplified SEBAL pipeline producing a daily ETa raster in mm/day."""
    hot_idx, cold_idx = select_anchor_pixels(inputs.ndvi, inputs.lst_kelvin)

    rn = compute_net_radiation(inputs)
    g = compute_soil_heat_flux(inputs.ndvi, inputs.albedo, inputs.lst_kelvin, rn)
    h = compute_sensible_heat_flux(rn, g, inputs.lst_kelvin, hot_idx, cold_idx)

    le = np.clip(rn - g - h, 0, None)  # latent heat flux, W/m^2
    eta_mm_day = (le * 86400) / LATENT_HEAT_VAPORIZATION

    logger.info(f"SEBAL ETa computed — mean={np.nanmean(eta_mm_day):.2f} mm/day, "
                f"max={np.nanmax(eta_mm_day):.2f} mm/day")

    return SEBALResult(
        eta_mm_day=eta_mm_day,
        net_radiation_wm2=rn,
        soil_heat_flux_wm2=g,
        sensible_heat_flux_wm2=h,
        hot_pixel_idx=hot_idx,
        cold_pixel_idx=cold_idx,
        is_fallback=False,
    )


def eta_from_mod16(mod16_et_kg_m2_8day: np.ndarray) -> SEBALResult:
    """
    Fallback path when thermal imagery (Landsat/Sentinel-3 LST) is unavailable
    for the target date. MOD16A2 delivers 8-day cumulative ET in kg/m^2
    (== mm over 8 days); divide by 8 for a daily-equivalent rate so it is
    directly comparable with the SEBAL daily output used elsewhere.
    """
    eta_mm_day = mod16_et_kg_m2_8day / 8.0
    logger.warning("Using MOD16A2 fallback for ETa — SEBAL thermal inputs unavailable")
    return SEBALResult(
        eta_mm_day=eta_mm_day,
        net_radiation_wm2=np.full_like(eta_mm_day, np.nan),
        soil_heat_flux_wm2=np.full_like(eta_mm_day, np.nan),
        sensible_heat_flux_wm2=np.full_like(eta_mm_day, np.nan),
        hot_pixel_idx=(0, 0),
        cold_pixel_idx=(0, 0),
        is_fallback=True,
    )
