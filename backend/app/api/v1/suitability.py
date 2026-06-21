from fastapi import APIRouter, Query, HTTPException
import httpx
import math

router = APIRouter(prefix="/suitability", tags=["Crop Suitability Analysis"])

@router.get("")
async def get_crop_suitability(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location")
):
    """
    Evaluates global crop suitability for Wheat, Rice, Cotton, and Sugarcane
    by matching real-time meteorology metrics from Open-Meteo against FAO standard agronomic thresholds.
    """
    try:
        # Fetch current weather parameters from Open-Meteo
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,rain_sum&timezone=auto"
        async with httpx.AsyncClient() as client:
            res = await client.get(weather_url)
            if res.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch live meteorology metrics.")
            weather_data = res.json()

        # Parse current temp & rain
        curr_temp = weather_data.get("current_weather", {}).get("temperature", 25.0)
        max_temp = weather_data.get("daily", {}).get("temperature_2m_max", [curr_temp + 3])[0]
        min_temp = weather_data.get("daily", {}).get("temperature_2m_min", [curr_temp - 3])[0]
        rain_sum = weather_data.get("daily", {}).get("rain_sum", [0.0])[0]

        mean_temp = (max_temp + min_temp) / 2.0

        # FAO standard range matching logic
        # 1. Wheat: Prefers 15°C - 23°C. Drastically falls above 32°C and below 5°C
        wheat_score = 1.0
        if mean_temp > 23:
            wheat_score = max(0.1, 1.0 - (mean_temp - 23) * 0.08)
        elif mean_temp < 15:
            wheat_score = max(0.1, 1.0 - (15 - mean_temp) * 0.08)
        
        # 2. Rice: Prefers 22°C - 32°C, needs high humidity/rainfall
        rice_score = 1.0
        if mean_temp > 32:
            rice_score = max(0.1, 1.0 - (mean_temp - 32) * 0.06)
        elif mean_temp < 22:
            rice_score = max(0.1, 1.0 - (22 - mean_temp) * 0.08)
        # Wet scaling factor: rain rewards rice suitability
        rice_score = min(1.0, rice_score * (1.0 + min(rain_sum, 20.0) * 0.01))

        # 3. Cotton: Prefers warm/hot weather (22°C - 35°C), tolerant to dry cycles
        cotton_score = 1.0
        if mean_temp > 35:
            cotton_score = max(0.1, 1.0 - (mean_temp - 35) * 0.06)
        elif mean_temp < 22:
            cotton_score = max(0.1, 1.0 - (22 - mean_temp) * 0.08)
        # Heavy rain slightly penalizes cotton quality
        if rain_sum > 15.0:
            cotton_score = max(0.3, cotton_score * 0.85)

        # 4. Sugarcane: Prefers tropical hot weather (24°C - 38°C), needs water
        sugarcane_score = 1.0
        if mean_temp > 38:
            sugarcane_score = max(0.1, 1.0 - (mean_temp - 38) * 0.07)
        elif mean_temp < 24:
            sugarcane_score = max(0.1, 1.0 - (24 - mean_temp) * 0.09)

        return {
            "coordinates": {"latitude": lat, "longitude": lon},
            "meteorology": {
                "mean_temperature": round(mean_temp, 1),
                "max_temperature": round(max_temp, 1),
                "min_temperature": round(min_temp, 1),
                "rain_sum_mm": round(rain_sum, 2)
            },
            "suitability_scores": [
                {
                    "crop": "wheat",
                    "score": round(wheat_score * 100, 1),
                    "status": "Optimal" if wheat_score > 0.75 else ("Moderate" if wheat_score > 0.4 else "Poor"),
                    "ideal_temp_range": "15°C - 23°C"
                },
                {
                    "crop": "rice",
                    "score": round(rice_score * 100, 1),
                    "status": "Optimal" if rice_score > 0.75 else ("Moderate" if rice_score > 0.4 else "Poor"),
                    "ideal_temp_range": "22°C - 32°C"
                },
                {
                    "crop": "cotton",
                    "score": round(cotton_score * 100, 1),
                    "status": "Optimal" if cotton_score > 0.75 else ("Moderate" if cotton_score > 0.4 else "Poor"),
                    "ideal_temp_range": "22°C - 35°C"
                },
                {
                    "crop": "sugarcane",
                    "score": round(sugarcane_score * 100, 1),
                    "status": "Optimal" if sugarcane_score > 0.75 else ("Moderate" if sugarcane_score > 0.4 else "Poor"),
                    "ideal_temp_range": "24°C - 38°C"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suitability analysis failed: {str(e)}")
