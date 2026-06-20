-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable TimescaleDB if available (will fail gracefully if not loaded, hence handled in Python or run separately)
-- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer', -- 'admin', 'operator', 'viewer'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Canal Command Areas (Water distribution zones)
CREATE TABLE IF NOT EXISTS command_areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity_cusec DOUBLE PRECISION DEFAULT 1000.0,
    current_flow_cusec DOUBLE PRECISION DEFAULT 0.0,
    geom geometry(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Canals (Water delivery networks)
CREATE TABLE IF NOT EXISTS canals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    command_area_id INTEGER REFERENCES command_areas(id) ON DELETE SET NULL,
    flow_rate_cusec DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'operational', -- 'operational', 'maintenance', 'dry'
    geom geometry(LineString, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fields / Plots Table
CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    village VARCHAR(255),
    district VARCHAR(255),
    soil_type VARCHAR(100) DEFAULT 'alluvial', -- 'alluvial', 'black', 'red', 'clay'
    command_area_id INTEGER REFERENCES command_areas(id) ON DELETE SET NULL,
    geom geometry(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Satellite Raster Metadata Table
CREATE TABLE IF NOT EXISTS rasters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sensor VARCHAR(50) NOT NULL, -- 'Sentinel-2', 'Sentinel-1', 'Landsat-8', etc.
    acquisition_date DATE NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    cloud_cover DOUBLE PRECISION DEFAULT 0.0,
    spatial_resolution DOUBLE PRECISION DEFAULT 10.0,
    geom geometry(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crop Classification Output
CREATE TABLE IF NOT EXISTS crop_classifications (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    crop_type VARCHAR(100) NOT NULL, -- 'wheat', 'rice', 'cotton', 'sugarcane', 'fallow'
    probability DOUBLE PRECISION NOT NULL,
    uncertainty DOUBLE PRECISION NOT NULL,
    classification_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Phenology Stages
CREATE TABLE IF NOT EXISTS phenological_stages (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    stage VARCHAR(100) NOT NULL, -- 'emergence', 'vegetative', 'flowering', 'reproductive', 'maturity', 'harvest'
    confidence DOUBLE PRECISION NOT NULL,
    detection_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Soil Moisture & Stress Time Series Table
CREATE TABLE IF NOT EXISTS soil_moisture_timeseries (
    id SERIAL,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ndvi DOUBLE PRECISION,
    ndwi DOUBLE PRECISION,
    soil_moisture DOUBLE PRECISION,
    stress_level VARCHAR(50) NOT NULL, -- 'No Stress', 'Mild Stress', 'Moderate Stress', 'Severe Stress', 'Critical Stress'
    stress_score DOUBLE PRECISION, -- 0.0 (no stress) to 1.0 (dead)
    PRIMARY KEY (id, timestamp)
);

-- Water Deficit Time Series Table (FAO-56 output)
CREATE TABLE IF NOT EXISTS water_deficit_timeseries (
    id SERIAL,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    et0 DOUBLE PRECISION, -- Reference ET mm/day
    etc DOUBLE PRECISION, -- Crop ET mm/day
    eta DOUBLE PRECISION, -- Actual ET mm/day
    water_deficit DOUBLE PRECISION, -- mm
    net_water_requirement DOUBLE PRECISION, -- mm
    PRIMARY KEY (id, timestamp)
);

-- Irrigation Advisories Table
CREATE TABLE IF NOT EXISTS irrigation_advisories (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    recommended_action VARCHAR(100) NOT NULL, -- 'Immediate irrigation', 'Irrigate in 2 days', 'Irrigate in 5 days', 'No irrigation required'
    recommended_depth_mm DOUBLE PRECISION NOT NULL,
    recommended_volume_m3 DOUBLE PRECISION NOT NULL,
    water_savings_m3 DOUBLE PRECISION NOT NULL,
    advisory_text TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending' -- 'pending', 'sent', 'failed'
);

-- System Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id) ON DELETE CASCADE,
    trigger_type VARCHAR(100) NOT NULL, -- 'moisture_stress', 'water_deficit', 'canal_shortage'
    severity VARCHAR(50) NOT NULL, -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'unread' -- 'unread', 'read', 'archived'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_fields_geom ON fields USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_command_areas_geom ON command_areas USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_canals_geom ON canals USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_rasters_geom ON rasters USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_soil_moisture_ts ON soil_moisture_timeseries (field_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_water_deficit_ts ON water_deficit_timeseries (field_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_crop_classifications ON crop_classifications (field_id, classification_date DESC);
CREATE INDEX IF NOT EXISTS idx_phenological_stages ON phenological_stages (field_id, detection_date DESC);
