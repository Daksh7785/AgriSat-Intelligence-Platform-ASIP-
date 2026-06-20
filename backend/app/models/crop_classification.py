from sqlalchemy import Column, String, Float, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class CropClassification(BaseModel):
    __tablename__ = "crop_classifications"

    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"))
    command_area_id = Column(UUID(as_uuid=True), ForeignKey("command_areas.id", ondelete="CASCADE"), nullable=True)
    season = Column(String(50), nullable=False, index=True)
    crop_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(50))
    classified_at = Column(Date, index=True)
    validated = Column(Boolean, default=False)
    validation_source = Column(String(100))

    # Relationships
    field = relationship("Field", back_populates="classifications")
    command_area = relationship("CommandArea", back_populates="crop_classifications")
