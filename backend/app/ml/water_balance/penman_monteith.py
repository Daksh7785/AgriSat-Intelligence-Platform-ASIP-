"""
FAO-56 Penman-Monteith Reference Evapotranspiration (ET0) and Crop Evapotranspiration (ETc) calculation.
"""
from __future__ import annotations
import numpy as np


def compute_eto(
    temp_c: float,
    wind_ms: float,
    rh_pct: float,
    solar_rad_wm2: float,
    elevation_m: float = 250.0,
) -> float:
    """
    Computes reference evapotranspiration (ET0) in mm/day.
    solar_rad_wm2 is converted to MJ/m^2/day: solar_rad_MJ = solar_rad_wm2 * 0.0864.
    """
    solar_rad_mj = solar_rad_wm2 * 0.0864
    
    # Atmospheric pressure
    p = 101.3 * (((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26)
    
    # Psychrometric constant
    gamma = 0.000665 * p
    
    # Slope of vapor pressure curve
    t_term = temp_c + 237.3
    delta = (4098.0 * (0.6108 * np.exp((17.27 * temp_c) / t_term))) / (t_term ** 2)
    
    # Saturation vapor pressure
    es = 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    
    # Actual vapor pressure
    ea = es * (rh_pct / 100.0)
    
    # Vapor pressure deficit
    vpd = es - ea
    
    # Net radiation estimation
    rn = solar_rad_mj * 0.75
    g = 0.0
    
    numerator = 0.408 * delta * (rn - g) + gamma * (900.0 / (temp_c + 273.0)) * wind_ms * vpd
    denominator = delta + gamma * (1.0 + 0.34 * wind_ms)
    
    et0 = numerator / denominator
    return float(max(0.0, et0))


def compute_etc(eto: float, kc: float) -> float:
    """Computes crop evapotranspiration under standard conditions (ETc = Kc * ET0)."""
    return float(max(0.0, eto * kc))
