from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import BaseModel

class Field(BaseModel):
    __tablename__ = "fields"

    command_area_id = Column(UUID(as_uuid=True), ForeignKey("command_areas.id", ondelete="SET NULL"), nullable=True)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="SET NULL"), nullable=True)
    geometry = Column(Geometry("POLYGON", srid=4326))
    area_hectares = Column(Float)
    soil_type = Column(String(50), default="alluvial")

    # Relationships
    command_area = relationship("CommandArea", back_populates="fields")
    farmer = relationship("Farmer", back_populates="fields")
    classifications = relationship("CropClassification", back_populates="field", cascade="all, delete-orphan")
    phenology_records = relationship("PhenologyRecord", back_populates="field", cascade="all, delete-orphan")
    stress_assessments = relationship("StressAssessment", back_populates="field", cascade="all, delete-orphan")
    advisories = relationship("IrrigationAdvisory", back_populates="field", cascade="all, delete-orphan")
