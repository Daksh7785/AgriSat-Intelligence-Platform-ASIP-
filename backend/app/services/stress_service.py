import numpy as np
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models

class StressService:
    STRESS_CLASSES = {
        1: "No Stress",
        2: "Mild Stress",
        3: "Moderate Stress",
        4: "Severe Stress",
        5: "Critical Stress"
    }

    @staticmethod
    def detect_moisture_stress(
        ndvi_anomaly: float,       # Deviation from long-term median (-1 to 1)
        ndwi_anomaly: float,       # Deviation from long-term median (-1 to 1)
        sar_moisture_index: float, # Deviation in VH/VV backscatter ratio (-5 to 5)
        rainfall_anomaly: float,   # Departure from normal rainfall (-1 to 1)
        temp_anomaly: float        # Land Surface Temp departure (-5 to 5)
    ) -> Dict[str, Any]:
        """
        AI stress engine combining multiple optical, SAR, and meteorological anomalies.
        Outputs classified stress levels and numerical stress scores [0.0 - 1.0].
        """
        # Score computation based on physical indicators:
        # Negative anomalies in greenness (NDVI) and wetness (NDWI) increase stress.
        # Positive temperature anomalies (heat stress) and negative rainfall anomalies increase stress.
        # SAR moisture index represents wetness; negative values indicate dry soil.
        
        # Normalize anomalies to standard contributions:
        # Higher score = more stress
        ndvi_score = max(0, -ndvi_anomaly) * 2.5       # weight 25%
        ndwi_score = max(0, -ndwi_anomaly) * 3.0       # weight 30%
        temp_score = max(0, temp_anomaly / 5.0) * 1.5   # weight 15%
        rain_score = max(0, -rainfall_anomaly) * 1.5   # weight 15%
        
        sar_score = 0.0
        if sar_moisture_index is not None:
            sar_score = max(0, -sar_moisture_index / 3.0) * 1.5  # weight 15%
            
        total_score = ndvi_score + ndwi_score + temp_score + rain_score + sar_score
        
        # Cap score at 1.0
        stress_score = float(np.clip(total_score, 0.0, 1.0))
        
        # Map score to 5 classes
        if stress_score < 0.15:
            stress_level_idx = 1
        elif stress_score < 0.35:
            stress_level_idx = 2
        elif stress_score < 0.60:
            stress_level_idx = 3
        elif stress_score < 0.80:
            stress_level_idx = 4
        else:
            stress_level_idx = 5
            
        stress_level = StressService.STRESS_CLASSES[stress_level_idx]
        
        return {
            "stress_score": stress_score,
            "stress_level": stress_level,
            "stress_level_code": stress_level_idx
        }

    @staticmethod
    def generate_village_reports(db: Session, district: str = None) -> List[Dict[str, Any]]:
        """
        Aggregates crop moisture stress indicators at the administrative village level.
        Enables targeting local relief and canal water distribution.
        """
        # Fetch the latest stress record for each field
        subquery = db.query(
            models.SoilMoistureTimeSeries.field_id,
            func.max(models.SoilMoistureTimeSeries.timestamp).label("max_ts")
        ).group_by(models.SoilMoistureTimeSeries.field_id).subquery()
        
        query = db.query(
            models.Field.village,
            models.Field.district,
            models.SoilMoistureTimeSeries.stress_level,
            models.SoilMoistureTimeSeries.stress_score
        ).join(
            models.SoilMoistureTimeSeries,
            models.Field.id == models.SoilMoistureTimeSeries.field_id
        ).join(
            subquery,
            (models.SoilMoistureTimeSeries.field_id == subquery.c.field_id) &
            (models.SoilMoistureTimeSeries.timestamp == subquery.c.max_ts)
        )
        
        if district:
            query = query.filter(models.Field.district == district)
            
        records = query.all()
        
        # Process village summaries
        village_data = {}
        for r in records:
            key = (r.village, r.district)
            if key not in village_data:
                village_data[key] = {
                    "village": r.village,
                    "district": r.district,
                    "total_fields": 0,
                    "stressed_fields": 0,
                    "stress_scores": [],
                    "critical_count": 0
                }
            
            summary = village_data[key]
            summary["total_fields"] += 1
            summary["stress_scores"].append(r.stress_score)
            
            if r.stress_level in ["Moderate Stress", "Severe Stress", "Critical Stress"]:
                summary["stressed_fields"] += 1
                if r.stress_level == "Critical Stress":
                    summary["critical_count"] += 1
                    
        reports = []
        for key, value in village_data.items():
            avg_score = float(np.mean(value["stress_scores"])) if value["stress_scores"] else 0.0
            pct_stressed = float(value["stressed_fields"] / value["total_fields"] * 100.0) if value["total_fields"] > 0 else 0.0
            
            reports.append({
                "village": value["village"],
                "district": value["district"],
                "total_fields": value["total_fields"],
                "stressed_fields": value["stressed_fields"],
                "pct_stressed": pct_stressed,
                "average_stress_score": avg_score,
                "critical_stress_fields": value["critical_count"],
                "advisory_priority": "High" if pct_stressed > 40.0 or avg_score > 0.60 else ("Medium" if pct_stressed > 15.0 else "Low")
            })
            
        # Sort by average stress score descending
        reports.sort(key=lambda x: x["average_stress_score"], reverse=True)
        return reports
