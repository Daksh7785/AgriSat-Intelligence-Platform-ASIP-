from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import json
from shapely.geometry import shape, mapping
from geoalchemy2.shape import to_shape
from typing import List, Dict, Any

from app.core.database import get_db
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/dashboard", tags=["Geospatial Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Computes summary statistics for the geospatial dashboard cards."""
    total_fields = db.query(models.Field).count()
    
    # Calculate average stress score
    avg_stress = db.query(func.avg(models.SoilMoistureTimeSeries.stress_score)).scalar() or 0.0
    
    # Calculate sum of water savings
    total_savings = db.query(func.sum(models.IrrigationAdvisory.water_savings_m3)).scalar() or 0.0
    
    # Calculate active canal flow
    total_canal_flow = db.query(func.sum(models.CommandArea.current_flow_cusec)).scalar() or 0.0
    
    # Calculate crop distribution counts
    crop_counts = db.query(
        models.CropClassification.crop_type,
        func.count(models.CropClassification.id)
    ).group_by(models.CropClassification.crop_type).all()
    
    crop_dist = {crop: count for crop, count in crop_counts}
    # Add defaults if empty
    for c in ['wheat', 'rice', 'cotton', 'sugarcane', 'fallow']:
        if c not in crop_dist:
            crop_dist[c] = 0
            
    return {
        "total_fields": total_fields,
        "average_stress_score": float(round(avg_stress, 2)),
        "total_water_saved_m3": float(round(total_savings, 1)),
        "active_command_canal_flow_cusec": float(round(total_canal_flow, 1)),
        "crop_distribution": crop_dist
    }

@router.get("/fields/geojson")
def get_fields_geojson(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Queries fields and returns them as a standard GeoJSON FeatureCollection."""
    fields = db.query(models.Field).all()
    features = []
    
    for f in fields:
        # Fetch latest crop and stress status
        crop = db.query(models.CropClassification).filter(
            models.CropClassification.field_id == f.id
        ).order_by(models.CropClassification.classification_date.desc()).first()
        
        stress = db.query(models.SoilMoistureTimeSeries).filter(
            models.SoilMoistureTimeSeries.field_id == f.id
        ).order_by(models.SoilMoistureTimeSeries.timestamp.desc()).first()
        
        geom = to_shape(f.geom)
        features.append({
            "type": "Feature",
            "id": f.id,
            "geometry": mapping(geom),
            "properties": {
                "name": f.name,
                "village": f.village,
                "district": f.district,
                "soil_type": f.soil_type,
                "crop_type": crop.crop_type if crop else "unknown",
                "stress_level": stress.stress_level if stress else "No Stress",
                "stress_score": stress.stress_score if stress else 0.0,
                "soil_moisture": stress.soil_moisture if stress else 0.5
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/command-areas/geojson")
def get_command_areas_geojson(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Queries command area boundaries and details as GeoJSON."""
    areas = db.query(models.CommandArea).all()
    features = []
    
    for a in areas:
        geom = to_shape(a.geom)
        features.append({
            "type": "Feature",
            "id": a.id,
            "geometry": mapping(geom),
            "properties": {
                "name": a.name,
                "capacity_cusec": a.capacity_cusec,
                "current_flow_cusec": a.current_flow_cusec,
                "utilization_pct": float(a.current_flow_cusec / a.capacity_cusec * 100.0) if a.capacity_cusec > 0 else 0.0
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/canals/geojson")
def get_canals_geojson(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Queries canal networks as LineString GeoJSON."""
    canals = db.query(models.Canal).all()
    features = []
    
    for c in canals:
        geom = to_shape(c.geom)
        features.append({
            "type": "Feature",
            "id": c.id,
            "geometry": mapping(geom),
            "properties": {
                "name": c.name,
                "flow_rate_cusec": c.flow_rate_cusec,
                "status": c.status
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }
