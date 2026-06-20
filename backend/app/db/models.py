from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommandArea(Base):
    __tablename__ = "command_areas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    capacity_cusec = Column(Float, default=1000.0)
    current_flow_cusec = Column(Float, default=0.0)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    canals = relationship("Canal", back_populates="command_area")
    fields = relationship("Field", back_populates="command_area")

class Canal(Base):
    __tablename__ = "canals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    command_area_id = Column(Integer, ForeignKey("command_areas.id", ondelete="SET NULL"), nullable=True)
    flow_rate_cusec = Column(Float, default=0.0)
    status = Column(String(50), default="operational")
    geom = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    command_area = relationship("CommandArea", back_populates="canals")

class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    village = Column(String(255))
    district = Column(String(255))
    soil_type = Column(String(100), default="alluvial")
    command_area_id = Column(Integer, ForeignKey("command_areas.id", ondelete="SET NULL"), nullable=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    command_area = relationship("CommandArea", back_populates="fields")
    classifications = relationship("CropClassification", back_populates="field", cascade="all, delete-orphan")
    phenologies = relationship("PhenologicalStage", back_populates="field", cascade="all, delete-orphan")
    soil_moisture_records = relationship("SoilMoistureTimeSeries", back_populates="field", cascade="all, delete-orphan")
    water_deficit_records = relationship("WaterDeficitTimeSeries", back_populates="field", cascade="all, delete-orphan")
    advisories = relationship("IrrigationAdvisory", back_populates="field", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="field", cascade="all, delete-orphan")

class Raster(Base):
    __tablename__ = "rasters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sensor = Column(String(50), nullable=False)
    acquisition_date = Column(Date, nullable=False)
    file_path = Column(String(512), nullable=False)
    cloud_cover = Column(Float, default=0.0)
    spatial_resolution = Column(Float, default=10.0)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CropClassification(Base):
    __tablename__ = "crop_classifications"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"))
    crop_type = Column(String(100), nullable=False)
    probability = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    classification_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    field = relationship("Field", back_populates="classifications")

class PhenologicalStage(Base):
    __tablename__ = "phenological_stages"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"))
    stage = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    detection_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    field = relationship("Field", back_populates="phenologies")

class SoilMoistureTimeSeries(Base):
    __tablename__ = "soil_moisture_timeseries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), primary_key=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    ndvi = Column(Float)
    ndwi = Column(Float)
    soil_moisture = Column(Float)
    stress_level = Column(String(50), nullable=False)
    stress_score = Column(Float)
    
    field = relationship("Field", back_populates="soil_moisture_records")

class WaterDeficitTimeSeries(Base):
    __tablename__ = "water_deficit_timeseries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), primary_key=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    et0 = Column(Float)
    etc = Column(Float)
    eta = Column(Float)
    water_deficit = Column(Float)
    net_water_requirement = Column(Float)
    
    field = relationship("Field", back_populates="water_deficit_records")

class IrrigationAdvisory(Base):
    __tablename__ = "irrigation_advisories"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    recommended_action = Column(String(100), nullable=False)
    recommended_depth_mm = Column(Float, nullable=False)
    recommended_volume_m3 = Column(Float, nullable=False)
    water_savings_m3 = Column(Float, nullable=False)
    advisory_text = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    
    field = relationship("Field", back_populates="advisories")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"))
    trigger_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="unread")
    
    field = relationship("Field", back_populates="alerts")


class AdvisoryFeedback(Base):
    __tablename__ = "advisory_feedback"
    id = Column(String(50), primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    advisory_id = Column(Integer, ForeignKey("irrigation_advisories.id", ondelete="CASCADE"), nullable=False)
    feedback_type = Column(String(50), nullable=False)
    submitted_by_role = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    corrected_crop_type = Column(String(100), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=func.now())

    field = relationship("Field")
    advisory = relationship("IrrigationAdvisory")


class ActiveLearningQueue(Base):
    __tablename__ = "active_learning_queue"
    id = Column(String(50), primary_key=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), unique=True, nullable=False)
    reason = Column(String(255), nullable=False)
    queued_at = Column(DateTime(timezone=True), default=func.now())

    field = relationship("Field")

