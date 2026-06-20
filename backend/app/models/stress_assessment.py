from sqlalchemy import Column, String, Date, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class StressAssessment(BaseModel):
    __tablename__ = "stress_assessments"

    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"))
    assessment_date = Column(Date, nullable=False, index=True)
    growth_stage = Column(String(50))
    ndvi = Column(Float)
    ndwi = Column(Float)
    vv_backscatter = Column(Float)
    vh_backscatter = Column(Float)
    vci = Column(Float)
    tci = Column(Float)
    vhi = Column(Float)
    stress_level = Column(String(20), nullable=False) # none, mild, moderate, severe
    stress_confidence = Column(Float, default=1.0)

    # Relationships
    field = relationship("Field", back_populates="stress_assessments")
