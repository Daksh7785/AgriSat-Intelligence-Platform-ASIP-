from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class CommandArea(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "command_areas"

    name = Column(String(200), nullable=False, index=True)
    short_code = Column(String(20), unique=True, nullable=False)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False)
    canal_system = Column(String(200))
    river_basin = Column(String(100))
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))
    area_hectares = Column(Float)
    bbox_west = Column(Float)
    bbox_south = Column(Float)
    bbox_east = Column(Float)
    bbox_north = Column(Float)
    crs_epsg = Column(Integer, default=32643)
    is_active = Column(Boolean, default=True)
    pilot_area = Column(Boolean, default=False)
    notes = Column(String(500))

    # Relationships
    fields = relationship("Field", back_populates="command_area")
    satellite_acquisitions = relationship(
        "SatelliteAcquisition", back_populates="command_area"
    )
    crop_classifications = relationship(
        "CropClassification", back_populates="command_area"
    )
