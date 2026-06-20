import numpy as np
from typing import Dict

class WaterService:
    # Crop Coefficients (Kc) table based on FAO-56 growth phases:
    # Stages: [emergence, vegetative, flowering, reproductive, maturity, harvest]
    KC_TABLE = {
        "wheat": [0.3, 0.7, 1.15, 1.15, 0.4, 0.15],
        "rice": [1.05, 1.1, 1.2, 1.2, 0.9, 0.2],
        "cotton": [0.35, 0.75, 1.2, 1.2, 0.6, 0.3],
        "sugarcane": [0.4, 0.9, 1.25, 1.25, 0.75, 0.5],
        "fallow": [0.15, 0.15, 0.15, 0.15, 0.15, 0.15]
    }

    @staticmethod
    def calculate_penman_monteith_et0(
        t_mean: float,       # Mean temperature (°C)
        t_max: float,        # Max temperature (°C)
        t_min: float,        # Min temperature (°C)
        wind_speed_2m: float, # Wind speed at 2m (m/s)
        solar_rad: float,    # Solar radiation (MJ/m^2/day)
        rel_humidity: float, # Relative humidity (%)
        elevation: float = 250.0  # Elevation in meters
    ) -> float:
        """
        Calculates reference evapotranspiration (ET0) using the FAO-56 Penman-Monteith equation.
        """
        # Atmospheric Pressure P (kPa)
        p = 101.3 * (((293.0 - 0.0065 * elevation) / 293.0) ** 5.26)
        
        # Psychrometric constant gamma (kPa/°C)
        gamma = 0.000665 * p
        
        # Slope of vapor pressure curve delta (kPa/°C)
        t_term = t_mean + 237.3
        delta = (4098.0 * (0.6108 * np.exp((17.27 * t_mean) / t_term))) / (t_term ** 2)
        
        # Saturation vapor pressure es (kPa)
        es_max = 0.6108 * np.exp((17.27 * t_max) / (t_max + 237.3))
        es_min = 0.6108 * np.exp((17.27 * t_min) / (t_min + 237.3))
        es = (es_max + es_min) / 2.0
        
        # Actual vapor pressure ea (kPa)
        ea = es * (rel_humidity / 100.0)
        
        # Saturation vapor pressure deficit (es - ea)
        vpd = es - ea
        
        # Soil heat flux G (assumed 0 for daily calculations)
        g = 0.0
        
        # Net Radiation Rn (typically Rn is ~70-80% of shortwave solar radiation)
        # For simplified robust calculation:
        rn = solar_rad * 0.75
        
        # FAO-56 Penman-Monteith Equation
        numerator = 0.408 * delta * (rn - g) + gamma * (900.0 / (t_mean + 273.0)) * wind_speed_2m * vpd
        denominator = delta + gamma * (1.0 + 0.34 * wind_speed_2m)
        
        et0 = numerator / denominator
        return float(max(0.0, et0))

    @staticmethod
    def get_crop_coefficient(crop_type: str, growth_stage: str) -> float:
        """Gets crop coefficient (Kc) mapped to phenological stages."""
        crop_lower = crop_type.lower()
        if crop_lower not in WaterService.KC_TABLE:
            crop_lower = "fallow"
            
        stage_map = {
            "emergence": 0,
            "vegetative": 1,
            "flowering": 2,
            "reproductive": 3,
            "maturity": 4,
            "harvest": 5
        }
        
        stage_idx = stage_map.get(growth_stage.lower(), 1)  # Default to vegetative
        return WaterService.KC_TABLE[crop_lower][stage_idx]

    @staticmethod
    def calculate_effective_rainfall(rainfall_mm: float) -> float:
        """Calculates effective rainfall using the USDA Soil Conservation Service method (scaled daily)."""
        # Daily scaling rule of thumb: Effective rain is 80% of rain above 2mm, capped at 85% of total
        if rainfall_mm < 2.0:
            return 0.0
        elif rainfall_mm <= 15.0:
            return float(0.8 * (rainfall_mm - 2.0))
        else:
            return float(0.7 * rainfall_mm)

    @staticmethod
    def estimate_crop_water_deficit(
        et0: float,
        crop_type: str,
        growth_stage: str,
        soil_moisture_fraction: float, # Soil moisture as fraction of field capacity [0.0, 1.0]
        rainfall_mm: float
    ) -> Dict[str, float]:
        """
        Executes Module 6 water deficit estimation.
        Returns: ET0, ETc, ETa, Water Deficit, Effective Rainfall, and Net Water Requirement.
        """
        kc = WaterService.get_crop_coefficient(crop_type, growth_stage)
        
        # Crop Evapotranspiration (ETc)
        etc = et0 * kc
        
        # Soil Moisture Stress Coefficient (Ks)
        # Ks is 1.0 down to 50% depletion, then drops linearly
        ks = 1.0
        depletion_threshold = 0.5
        if soil_moisture_fraction < depletion_threshold:
            ks = soil_moisture_fraction / depletion_threshold
        ks = np.clip(ks, 0.0, 1.0)
        
        # Actual Evapotranspiration (ETa)
        eta = etc * ks
        
        # Water Deficit
        water_deficit = etc - eta
        
        # Effective rainfall contribution
        effective_rain = WaterService.calculate_effective_rainfall(rainfall_mm)
        
        # Net Water Requirement (NWR)
        nwr = max(0.0, etc - effective_rain)
        
        return {
            "et0": float(et0),
            "etc": float(etc),
            "eta": float(eta),
            "water_deficit": float(water_deficit),
            "effective_rainfall": float(effective_rain),
            "net_water_requirement": float(nwr)
        }
