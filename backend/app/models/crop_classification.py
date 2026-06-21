"""Per-field crop type classification results, one row per field per season."""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CropClassification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "crop_classifications"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    season: Mapped[str] = mapped_column(String(50))              # 'Kharif-2025', 'Rabi-2025-26'
    crop_type: Mapped[str] = mapped_column(String(100))
    confidence_score: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50))
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ground_truth_is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
