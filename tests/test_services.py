import pytest
import numpy as np
from app.services.water_service import WaterService
from app.services.stress_service import StressService
from app.services.advisory_service import AdvisoryService
from app.services.raster_service import RasterService

def test_penman_monteith_et0():
    # Test typical summer day parameters in India
    et0 = WaterService.calculate_penman_monteith_et0(
        t_mean=29.0,
        t_max=35.0,
        t_min=23.0,
        wind_speed_2m=2.5,
        solar_rad=24.0,
        rel_humidity=60.0
    )
    assert et0 > 0.0
    # Evapotranspiration on a hot dry day should be significant (typically 4-8 mm)
    assert 3.0 <= et0 <= 9.0

def test_effective_rainfall():
    # Under 2mm should return 0
    assert WaterService.calculate_effective_rainfall(1.5) == 0.0
    # Over 2mm
    assert WaterService.calculate_effective_rainfall(10.0) > 0.0

def test_moisture_stress_scoring():
    # Critical anomalies (negative NDVI and NDWI anomalies)
    res = StressService.detect_moisture_stress(
        ndvi_anomaly=-0.4,
        ndwi_anomaly=-0.3,
        sar_moisture_index=-2.5,
        rainfall_anomaly=-0.8,
        temp_anomaly=4.5
    )
    assert res["stress_level"] in ["Severe Stress", "Critical Stress"]
    assert res["stress_score"] > 0.70

def test_advisory_logic():
    # Under severe stress, advise immediate watering
    res = AdvisoryService.generate_irrigation_advisory(
        crop_type="wheat",
        growth_stage="flowering",
        soil_moisture_fraction=0.20,
        water_deficit_mm=5.5,
        forecast_rainfall_7d_mm=0.0
    )
    assert res["recommended_action"] == "Immediate irrigation"
    assert res["recommended_depth_mm"] > 40.0
    
    # Under saturated soil or incoming rain, advise none
    res_rain = AdvisoryService.generate_irrigation_advisory(
        crop_type="wheat",
        growth_stage="flowering",
        soil_moisture_fraction=0.85,
        water_deficit_mm=0.5,
        forecast_rainfall_7d_mm=25.0
    )
    assert res_rain["recommended_action"] == "No irrigation required"
    assert res_rain["recommended_depth_mm"] == 0.0

def test_spectral_indices():
    # Mock array calculations
    blue = np.array([0.08, 0.06])
    green = np.array([0.12, 0.10])
    red = np.array([0.07, 0.05])
    nir = np.array([0.45, 0.48])
    swir = np.array([0.18, 0.15])
    
    indices = RasterService.compute_vegetation_indices(blue, green, red, nir, swir)
    assert 0.0 < indices["ndvi"] < 1.0
    assert 0.0 < indices["evi"] < 1.0
    assert 0.0 < indices["savi"] < 1.0
