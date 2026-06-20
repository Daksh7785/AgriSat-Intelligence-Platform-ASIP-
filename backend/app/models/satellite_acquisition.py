from sqlalchemy import Column, String, Date, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class SatelliteAcquisition(BaseModel):
    __tablename__ = "satellite_acquisitions"

    satellite = Column(String(50), nullable=False) # Sentinel-2, Landsat-8, Sentinel-1
    acquisition_date = Column(Date, nullable=False, index=True)
    command_area_id = Column(UUID(as_uuid=True), ForeignKey("command_areas.id", ondelete="CASCADE"))
    cloud_cover_pct = Column(Float, default=0.0)
    data_path = Column(String(500), nullable=False)
    processing_status = Column(String(50), default="pending") # pending, success, failed

    # Relationships
    command_area = relationship("CommandArea", back_populates="satellite_acquisitions")
