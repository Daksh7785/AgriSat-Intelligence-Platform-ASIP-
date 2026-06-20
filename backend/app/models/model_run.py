from sqlalchemy import Column, String, Date, Float, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ModelRun(BaseModel):
    __tablename__ = "model_runs"

    run_date = Column(Date, nullable=False, index=True)
    command_area_id = Column(UUID(as_uuid=True), ForeignKey("command_areas.id", ondelete="CASCADE"))
    model_version = Column(String(50), nullable=False)
    overall_accuracy = Column(Float)
    kappa_coefficient = Column(Float)
    f1_per_class = Column(JSON)
    processing_duration_seconds = Column(Integer)
    pixels_processed = Column(Integer)
    status = Column(String(50), default="completed") # completed, failed, running

    # Relationships
    # None explicit required unless referenced by other log operations
