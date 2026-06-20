import datetime
from typing import Dict, Any

class AdvisoryService:
    @staticmethod
    def generate_irrigation_advisory(
        crop_type: str,
        growth_stage: str,
        soil_moisture_fraction: float, # Soil moisture [0.0 - 1.0]
        water_deficit_mm: float,       # mm/day water deficit
        forecast_rainfall_7d_mm: float, # 7-day forecast rainfall sum
        field_area_ha: float = 1.5      # Hectares
    ) -> Dict[str, Any]:
        """
        Decision engine representing Module 7.
        Calculates recommended timing, depth, volume, and potential water savings.
        """
        crop_lower = crop_type.lower()
        stage_lower = growth_stage.lower()
        
        # Base traditional flooding depth (mm) for comparison
        traditional_flood_depth = 75.0 # standard 3-inch flooding depth
        
        # Determine urgency based on stress and rainfall
        # Critical thresholds:
        if soil_moisture_fraction < 0.35 and forecast_rainfall_7d_mm < 5.0:
            recommended_action = "Immediate irrigation"
            # Depleted. Need to replenish root zone. Recommend 50-60mm depending on crop
            rec_depth = 55.0
        elif soil_moisture_fraction < 0.50 and forecast_rainfall_7d_mm < 10.0:
            recommended_action = "Irrigate in 2 days"
            rec_depth = 40.0
        elif soil_moisture_fraction < 0.65 and forecast_rainfall_7d_mm < 15.0:
            recommended_action = "Irrigate in 5 days"
            rec_depth = 30.0
        else:
            recommended_action = "No irrigation required"
            rec_depth = 0.0
            
        # Adjust depth based on crop type & growth stages
        # e.g., Sugarcane needs more water, Fallow needs none
        if crop_lower == "fallow" or stage_lower == "harvest":
            recommended_action = "No irrigation required"
            rec_depth = 0.0
        elif crop_lower == "sugarcane" and rec_depth > 0:
            rec_depth += 10.0
        elif crop_lower == "rice" and rec_depth > 0:
            # Rice prefers saturated soil (submerged)
            rec_depth += 15.0
            if recommended_action == "Irrigate in 5 days":
                recommended_action = "Irrigate in 2 days"
                
        # Calculate volume: 1 mm = 10 m^3/ha
        recommended_volume_m3 = rec_depth * 10.0 * field_area_ha
        
        # Estimate Water Savings (difference between traditional flooding and precision advisory)
        if rec_depth > 0 and rec_depth < traditional_flood_depth:
            water_savings_m3 = (traditional_flood_depth - rec_depth) * 10.0 * field_area_ha
        elif recommended_action == "No irrigation required" and soil_moisture_fraction < 0.65:
            # Saved a full flooding event due to upcoming rainfall forecast
            water_savings_m3 = traditional_flood_depth * 10.0 * field_area_ha
        else:
            water_savings_m3 = 0.0
            
        # Build textual advisory
        if recommended_action == "Immediate irrigation":
            advisory_text = (
                f"Critical moisture depletion detected in {crop_type} crop during the {growth_stage} stage. "
                f"Apply {rec_depth:.1f} mm of water immediately to avoid yield loss. "
                f"Expected net water demand is {water_deficit_mm:.1f} mm/day. No significant rainfall is forecast."
            )
        elif recommended_action == "Irrigate in 2 days":
            advisory_text = (
                f"Moderate soil moisture depletion in {crop_type} ({growth_stage} stage). "
                f"Schedule irrigation of {rec_depth:.1f} mm within the next 48 hours. "
                f"Forecast rainfall is low ({forecast_rainfall_7d_mm:.1f} mm)."
            )
        elif recommended_action == "Irrigate in 5 days":
            advisory_text = (
                f"Soil moisture is adequate for now, but declining. Plan to irrigate {rec_depth:.1f} mm in 5 days "
                f"unless rainfall exceeds 15mm in the meantime."
            )
        else:
            if forecast_rainfall_7d_mm >= 15.0:
                advisory_text = (
                    f"No irrigation required. Upcoming rainfall of {forecast_rainfall_7d_mm:.1f} mm is sufficient "
                    f"to meet the water requirements of {crop_type} during the {growth_stage} stage."
                )
            elif crop_lower == "fallow":
                advisory_text = "Field is currently fallow. No irrigation required."
            elif stage_lower == "harvest":
                advisory_text = "Crop is in harvest stage. Withhold irrigation to facilitate drying and harvesting operations."
            else:
                advisory_text = "Soil moisture levels are optimal. No irrigation required at this time."
                
        return {
            "recommended_action": recommended_action,
            "recommended_depth_mm": float(rec_depth),
            "recommended_volume_m3": float(recommended_volume_m3),
            "water_savings_m3": float(water_savings_m3),
            "advisory_text": advisory_text
        }
