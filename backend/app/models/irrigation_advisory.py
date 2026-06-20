from sqlalchemy import Column, String, Date, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class IrrigationAdvisory(BaseModel):
    __tablename__ = "irrigation_advisories"

    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"))
    advisory_date = Column(Date, nullable=False, index=True)
    valid_from = Column(Date)
    valid_to = Column(Date)
    etc_mm = Column(Float)
    eta_mm = Column(Float)
    effective_rainfall_mm = Column(Float)
    water_deficit_mm = Column(Float)
    irrigation_requirement_mm = Column(Float)
    advisory_class = Column(String(20), default="none") # none, light, moderate, urgent, critical
    advisory_text_en = Column(Text)
    advisory_text_hi = Column(Text)
    advisory_text_local = Column(Text)
    delivered_sms = Column(Boolean, default=False)
    delivered_whatsapp = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    field = relationship("Field", back_populates="advisories")
