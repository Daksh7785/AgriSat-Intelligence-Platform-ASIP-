import datetime
import random
from typing import List, Tuple, Any
from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape
from app.db import models
from loguru import logger

async def generate_sample_data_for_bbox(
    bbox: Tuple[float, float, float, float],
    crops: List[str],
    command_area_id: int,
    season_label: str,
    db: Any
) -> List[models.Field]:
    """
    Generates 4 mock fields in a grid inside the bounding box and seeds
    crop classification, phenology, soil moisture, and water deficit records
    for each.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    lon_mid = (min_lon + max_lon) / 2
    lat_mid = (min_lat + max_lat) / 2
    
    quadrants = [
        [(min_lon, min_lat), (lon_mid, min_lat), (lon_mid, lat_mid), (min_lon, lat_mid), (min_lon, min_lat)],
        [(lon_mid, min_lat), (max_lon, min_lat), (max_lon, lat_mid), (lon_mid, lat_mid), (lon_mid, min_lat)],
        [(min_lon, lat_mid), (lon_mid, lat_mid), (lon_mid, max_lat), (min_lon, max_lat), (min_lon, lat_mid)],
        [(lon_mid, lat_mid), (max_lon, lat_mid), (max_lon, max_lat), (lon_mid, max_lat), (lon_mid, lat_mid)]
    ]
    
    fields = []
    today = datetime.datetime.now(datetime.timezone.utc)
    
    for i, coords in enumerate(quadrants):
        crop = crops[i % len(crops)] if crops else "wheat"
        poly = Polygon(coords)
        
        field = models.Field(
            name=f"Onboarded Field {i+1} ({crop.capitalize()})",
            village="Demo Village",
            district="Demo District",
            soil_type="alluvial",
            command_area_id=command_area_id,
            geom=from_shape(poly, srid=4326)
        )
        if db is not None:
            db.add(field)
        fields.append((field, crop))
        
    if db is not None:
        try:
            if hasattr(db, "flush"):
                try:
                    await db.flush()
                except (AttributeError, TypeError):
                    db.flush()
        except Exception as e:
            logger.warning(f"Database flush failed: {e}")
            
    for idx, (field, crop) in enumerate(fields):
        # Fallback ID for testing scenarios
        if field.id is None:
            field.id = 1000 + idx
            
        db_class = models.CropClassification(
            field_id=field.id,
            crop_type=crop,
            probability=0.90,
            uncertainty=0.05,
            classification_date=today.date()
        )
        
        db_stage = models.PhenologicalStage(
            field_id=field.id,
            stage="vegetative",
            confidence=0.85,
            detection_date=today.date()
        )
        
        if db is not None:
            db.add(db_class)
            db.add(db_stage)
        
        # 10 days of timeseries data
        for day in range(10):
            timestamp = today - datetime.timedelta(days=day)
            
            db_sm = models.SoilMoistureTimeSeries(
                field_id=field.id,
                timestamp=timestamp,
                ndvi=0.60 - 0.01 * day,
                ndwi=0.20 - 0.005 * day,
                soil_moisture=0.40 - 0.01 * day,
                stress_level="No Stress" if day < 5 else "Light Stress",
                stress_score=0.1 if day < 5 else 0.35
            )
            
            db_wd = models.WaterDeficitTimeSeries(
                field_id=field.id,
                timestamp=timestamp,
                et0=4.0,
                etc=3.5,
                eta=3.2,
                water_deficit=1.5 if day >= 5 else 0.2,
                net_water_requirement=2.0 if day >= 5 else 0.0
            )
            
            if db is not None:
                db.add(db_sm)
                db.add(db_wd)
                
    if db is not None:
        try:
            if hasattr(db, "commit"):
                try:
                    await db.commit()
                except (AttributeError, TypeError):
                    db.commit()
        except Exception as e:
            logger.error(f"Failed to commit onboarding sample data: {e}")
            
    return [f[0] for f in fields]
