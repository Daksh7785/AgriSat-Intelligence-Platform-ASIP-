from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import sys
import os

# Ensure app is on path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, ingestion, features, classification, stress, water, advisory, dashboard, copilot, alerts
from app.api.v1 import (
    irrigation_advisory,
    stress_detection,
    phenology,
    auth as auth_v1,
    explainability,
    uncertainty,
    drought,
    yield_forecast,
    roi,
    zonation,
    rotation,
    voice_advisory,
    feedback,
    onboarding,
    data_quality
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(ingestion.router, prefix=settings.API_V1_STR)
app.include_router(features.router, prefix=settings.API_V1_STR)
app.include_router(classification.router, prefix=settings.API_V1_STR)
app.include_router(stress.router, prefix=settings.API_V1_STR)
app.include_router(water.router, prefix=settings.API_V1_STR)
app.include_router(advisory.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(copilot.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)

# Register new v1 routers
app.include_router(irrigation_advisory.router, prefix=settings.API_V1_STR)
app.include_router(stress_detection.router, prefix=settings.API_V1_STR)
app.include_router(phenology.router, prefix=settings.API_V1_STR)
app.include_router(auth_v1.router, prefix=settings.API_V1_STR)
app.include_router(explainability.router, prefix=settings.API_V1_STR)
app.include_router(uncertainty.router, prefix=settings.API_V1_STR)
app.include_router(drought.router, prefix=settings.API_V1_STR)
app.include_router(yield_forecast.router, prefix=settings.API_V1_STR)
app.include_router(roi.router, prefix=settings.API_V1_STR)
app.include_router(zonation.router, prefix=settings.API_V1_STR)
app.include_router(rotation.router, prefix=settings.API_V1_STR)
app.include_router(voice_advisory.router, prefix=settings.API_V1_STR)
app.include_router(feedback.router, prefix=settings.API_V1_STR)
app.include_router(onboarding.router, prefix=settings.API_V1_STR)
app.include_router(data_quality.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def startup_event():
    """Initializes the database schema and seeds demo dataset if empty."""
    print("FastAPI Application Starting Up...")
    try:
        # Create PostGIS extension if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            print("PostGIS extension checked/created successfully.")
    except Exception as e:
        print(f"Error checking PostGIS extension: {e}. Ensure database user has superuser privileges.")
        
    try:
        # Create all tables defined in SQLAlchemy
        Base.metadata.create_all(bind=engine)
        print("SQLAlchemy tables created successfully.")
        
        # Check if seeder is required (if fields are empty)
        from sqlalchemy.orm import Session
        db = Session(bind=engine)
        field_count = db.execute(text("SELECT COUNT(*) FROM fields;")).scalar()
        
        if field_count == 0 and settings.DEMO_MODE:
            print("Database is empty. Running GIS seed pipeline...")
            from gis_pipeline.seed_db import seed_demo_data
            seed_demo_data(db)
            print("GIS database seeding completed.")
        db.close()
        
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "mode": "DEMO_MODE" if settings.DEMO_MODE else "PRODUCTION"
    }
