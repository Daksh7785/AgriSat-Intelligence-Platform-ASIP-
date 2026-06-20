from sqlalchemy import Column, String, Date, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class PhenologyRecord(BaseModel):
    __tablename__ = "phenology_records"

    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"))
    crop_type = Column(String(100), nullable=False)
    sowing_date = Column(Date)
    current_stage = Column(String(50), nullable=False)
    stage_start_date = Column(Date)
    days_since_sowing = Column(Integer)
    gdd_accumulated = Column(Float, default=0.0)

    # Relationships
    field = relationship("Field", back_populates="phenology_records")
