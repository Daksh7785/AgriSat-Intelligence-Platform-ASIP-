from sqlalchemy.orm import Session
from sqlalchemy import text
from shapely.geometry import Polygon, MultiPolygon, LineString
from geoalchemy2.shape import from_shape
import datetime

from app.core import security
from app.db import models

def seed_demo_data(db: Session):
    """Seeds database with a fully functional GIS and time series testing sandbox."""
    
    # 1. Seed Users
    hashed_pw = security.get_password_hash("adminpass")
    admin_user = models.User(
        email="admin@agrisense.ai",
        hashed_password=hashed_pw,
        role="admin"
    )
    db.add(admin_user)
    
    # 2. Seed Command Area (Bhakra Link Command, Punjab, India)
    # Coordinate box around 75.0, 30.0 to 75.2, 30.2
    poly_command = Polygon([
        (75.00, 30.00),
        (75.20, 30.00),
        (75.20, 30.20),
        (75.00, 30.20),
        (75.00, 30.00)
    ])
    multi_command = MultiPolygon([poly_command])
    
    command_area = models.CommandArea(
        name="Sirhind-Bhakra Command Zone",
        capacity_cusec=1500.0,
        current_flow_cusec=1250.0,
        geom=from_shape(multi_command, srid=4326)
    )
    db.add(command_area)
    db.commit()
    db.refresh(command_area)
    
    # 3. Seed Canals
    line_canal1 = LineString([(75.00, 30.10), (75.10, 30.10), (75.20, 30.15)])
    line_canal2 = LineString([(75.10, 30.10), (75.12, 30.02), (75.18, 30.01)])
    
    canal1 = models.Canal(
        name="Sirhind Feeder Canal",
        command_area_id=command_area.id,
        flow_rate_cusec=800.0,
        status="operational",
        geom=from_shape(line_canal1, srid=4326)
    )
    
    canal2 = models.Canal(
        name="Bhakra Distributary Branch",
        command_area_id=command_area.id,
        flow_rate_cusec=450.0,
        status="operational",
        geom=from_shape(line_canal2, srid=4326)
    )
    db.add_all([canal1, canal2])
    
    # 4. Seed Fields (Farms clustered around canals)
    field_coords = [
        # Field 1
        [(75.02, 30.02), (75.05, 30.02), (75.05, 30.05), (75.02, 30.05), (75.02, 30.02)],
        # Field 2
        [(75.06, 30.02), (75.09, 30.02), (75.09, 30.05), (75.06, 30.05), (75.06, 30.02)],
        # Field 3
        [(75.11, 30.03), (75.14, 30.03), (75.14, 30.06), (75.11, 30.06), (75.11, 30.03)],
        # Field 4
        [(75.15, 30.04), (75.19, 30.04), (75.19, 30.08), (75.15, 30.08), (75.15, 30.04)],
        # Field 5
        [(75.02, 30.12), (75.05, 30.12), (75.05, 30.16), (75.02, 30.16), (75.02, 30.12)],
        # Field 6
        [(75.06, 30.12), (75.09, 30.12), (75.09, 30.16), (75.06, 30.16), (75.06, 30.12)],
        # Field 7
        [(75.12, 30.11), (75.16, 30.11), (75.16, 30.15), (75.12, 30.15), (75.12, 30.11)]
    ]
    
    fields_list = []
    names = ["Harpreet Farm A", "Rajinder Farm B", "Gurcharan Plot", "Sandhu Field", "Punjab Agri Research Unit", "Majha Cooperative Farm", "Doaba Organic Field"]
    villages = ["Bathinda East", "Bathinda East", "Maur Kalan", "Maur Kalan", "Faridkot South", "Faridkot South", "Kotkapura North"]
    districts = ["Bathinda", "Bathinda", "Bathinda", "Bathinda", "Faridkot", "Faridkot", "Faridkot"]
    soils = ["alluvial", "alluvial", "black", "alluvial", "clay", "alluvial", "black"]
    
    for i, coords in enumerate(field_coords):
        poly_field = Polygon(coords)
        field = models.Field(
            name=names[i],
            village=villages[i],
            district=districts[i],
            soil_type=soils[i],
            command_area_id=command_area.id,
            geom=from_shape(poly_field, srid=4326)
        )
        db.add(field)
        fields_list.append(field)
        
    db.commit()
    for f in fields_list:
        db.refresh(f)
        
    # 5. Seed Historical Time Series (30 days of data for each field)
    crops = ["wheat", "rice", "cotton", "sugarcane", "fallow", "wheat", "rice"]
    stages = ["flowering", "vegetative", "reproductive", "maturity", "harvest", "flowering", "emergence"]
    
    today = datetime.datetime.now(datetime.timezone.utc)
    
    for idx, field in enumerate(fields_list):
        crop = crops[idx]
        stage = stages[idx]
        
        # Add Crop Classification entry
        db_class = models.CropClassification(
            field_id=field.id,
            crop_type=crop,
            probability=0.92 if crop != "fallow" else 0.98,
            uncertainty=0.04,
            classification_date=(today - datetime.timedelta(days=15)).date()
        )
        
        # Add Phenological stage entry
        db_stage = models.PhenologicalStage(
            field_id=field.id,
            stage=stage,
            confidence=0.89,
            detection_date=(today - datetime.timedelta(days=2)).date()
        )
        db.add_all([db_class, db_stage])
        
        # Generate 30 days of daily features
        for day in range(30):
            timestamp = today - datetime.timedelta(days=day)
            
            # Simulated indices curves
            # Add some stress variation to show up on dashboard
            if idx == 0 and day < 5:  # Wheat field experiences high stress recently
                ndvi = 0.35
                ndwi = -0.12
                soil_moisture = 0.22
                stress_level = "Severe Stress"
                stress_score = 0.72
                water_deficit = 6.2
                net_water_req = 7.5
            elif idx == 3 and day < 8: # Cotton field has moderate stress
                ndvi = 0.42
                ndwi = -0.05
                soil_moisture = 0.31
                stress_level = "Moderate Stress"
                stress_score = 0.51
                water_deficit = 4.5
                net_water_req = 5.0
            else: # Optimal conditions
                ndvi = 0.65 - 0.005 * day
                ndwi = 0.25 - 0.002 * day
                soil_moisture = 0.60 + 0.005 * (day % 3 - 1)
                stress_level = "No Stress"
                stress_score = 0.08
                water_deficit = 1.2
                net_water_req = 0.0
                
            db_sm = models.SoilMoistureTimeSeries(
                field_id=field.id,
                timestamp=timestamp,
                ndvi=ndvi,
                ndwi=ndwi,
                soil_moisture=soil_moisture,
                stress_level=stress_level,
                stress_score=stress_score
            )
            
            db_wd = models.WaterDeficitTimeSeries(
                field_id=field.id,
                timestamp=timestamp,
                et0=4.5,
                etc=4.5 * 0.85,
                eta=4.5 * 0.85 * (1.0 if stress_score < 0.2 else 0.7),
                water_deficit=water_deficit,
                net_water_requirement=net_water_req
            )
            
            db.add_all([db_sm, db_wd])
            
        # Seed an irrigation advisory for each field
        db_adv = models.IrrigationAdvisory(
            field_id=field.id,
            timestamp=today - datetime.timedelta(days=1),
            recommended_action="Immediate irrigation" if idx in [0, 3] else "No irrigation required",
            recommended_depth_mm=50.0 if idx in [0, 3] else 0.0,
            recommended_volume_m3=75.0 * 10 * 1.5 if idx in [0, 3] else 0.0,
            water_savings_m3=37.5 * 10 * 1.5 if idx in [0, 3] else 0.0,
            advisory_text="Immediate irrigation required due to severe moisture depletion." if idx in [0, 3] else "Soil moisture is optimal.",
            status="sent",
            sent_at=today - datetime.timedelta(days=1)
        )
        db.add(db_adv)
        
    db.commit()
