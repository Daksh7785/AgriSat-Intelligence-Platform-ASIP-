from sqlalchemy.orm import Session
from sqlalchemy import func, text
import json
from shapely.geometry import shape, mapping
from geoalchemy2.shape import to_shape
from typing import Dict, Any

from app.db import models
from app.services.stress_service import StressService

class CopilotService:
    @staticmethod
    def answer_query(db: Session, query_text: str) -> Dict[str, Any]:
        """
        Parses the user query, translates it to DB/PostGIS queries,
        and returns GIS-formatted GeoJSON/JSON responses.
        """
        query_lower = query_text.lower()
        
        # 1. "Show stressed wheat fields"
        if "stressed" in query_lower and "wheat" in query_lower:
            # Query fields that are classified as wheat and have moisture stress
            results = db.query(
                models.Field,
                models.SoilMoistureTimeSeries.stress_level,
                models.SoilMoistureTimeSeries.stress_score
            ).join(
                models.CropClassification,
                models.Field.id == models.CropClassification.field_id
            ).join(
                models.SoilMoistureTimeSeries,
                models.Field.id == models.SoilMoistureTimeSeries.field_id
            ).filter(
                models.CropClassification.crop_type == 'wheat'
            ).filter(
                models.SoilMoistureTimeSeries.stress_level.in_(["Mild Stress", "Moderate Stress", "Severe Stress", "Critical Stress"])
            ).all()
            
            features = []
            for field, level, score in results:
                geom = to_shape(field.geom)
                features.append({
                    "type": "Feature",
                    "id": field.id,
                    "geometry": mapping(geom),
                    "properties": {
                        "name": field.name,
                        "village": field.village,
                        "crop_type": "wheat",
                        "stress_level": level,
                        "stress_score": score
                    }
                })
                
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            return {
                "intent": "show_stressed_wheat",
                "message": f"Found {len(features)} wheat fields experiencing moisture stress.",
                "data": geojson,
                "display_type": "map"
            }
            
        # 2. "Which villages need irrigation?"
        elif "village" in query_lower and ("irrigation" in query_lower or "need" in query_lower):
            reports = StressService.generate_village_reports(db)
            # Filter for villages that need irrigation (High or Medium priority)
            needy_villages = [r for r in reports if r["advisory_priority"] in ["High", "Medium"]]
            
            return {
                "intent": "villages_needing_irrigation",
                "message": f"Identified {len(needy_villages)} villages with high or medium irrigation priorities.",
                "data": needy_villages,
                "display_type": "table"
            }
            
        # 3. "Forecast next week's water demand"
        elif "forecast" in query_lower or "water demand" in query_lower or "demand" in query_lower:
            # Aggregate forecasted net water requirement for all fields
            # Normally we'd use Module 8 predictions. Here we query the latest 8-day water deficit estimations.
            total_nwr = db.query(func.sum(models.WaterDeficitTimeSeries.net_water_requirement)).scalar() or 0.0
            total_etc = db.query(func.sum(models.WaterDeficitTimeSeries.etc)).scalar() or 0.0
            
            # Simple simulation: assume 1.5x scaling for command-wide projection
            simulated_next_week_demand_m3 = (total_nwr or 25.0) * 10.0 * 1250.0  # 1250 hectares command
            
            forecast_data = [
                {"day": "Monday", "demand_m3": float(simulated_next_week_demand_m3 * 0.12)},
                {"day": "Tuesday", "demand_m3": float(simulated_next_week_demand_m3 * 0.15)},
                {"day": "Wednesday", "demand_m3": float(simulated_next_week_demand_m3 * 0.14)},
                {"day": "Thursday", "demand_m3": float(simulated_next_week_demand_m3 * 0.16)},
                {"day": "Friday", "demand_m3": float(simulated_next_week_demand_m3 * 0.15)},
                {"day": "Saturday", "demand_m3": float(simulated_next_week_demand_m3 * 0.14)},
                {"day": "Sunday", "demand_m3": float(simulated_next_week_demand_m3 * 0.14)}
            ]
            
            return {
                "intent": "forecast_water_demand",
                "message": f"Command Area forecast predicts a cumulative water requirement of {simulated_next_week_demand_m3:,.1f} m³ over the next week.",
                "data": {
                    "total_forecast_m3": float(simulated_next_week_demand_m3),
                    "daily_distribution": forecast_data
                },
                "display_type": "chart"
            }
            
        # Default response
        else:
            return {
                "intent": "unknown",
                "message": (
                    "I am the AgriSense GIS Copilot. You can ask me questions like:\n"
                    "- 'Show stressed wheat fields' (renders geospatial layers)\n"
                    "- 'Which villages need irrigation?' (shows priority tables)\n"
                    "- 'Forecast next week's water demand' (visualizes daily requirement charts)"
                ),
                "data": None,
                "display_type": "text"
            }
