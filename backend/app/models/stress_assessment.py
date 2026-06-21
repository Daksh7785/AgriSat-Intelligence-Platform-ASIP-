"""Per-acquisition moisture stress assessment per field."""
from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import String, Float, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StressAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stress_assessments"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    assessment_date: Mapped[date] = mapped_column(Date)
    growth_stage: Mapped[str] = mapped_column(String(50))
    ndvi: Mapped[float] = mapped_column(Float)
    ndwi: Mapped[float] = mapped_column(Float)
    vv_backscatter: Mapped[float | None] = mapped_column(Float, nullable=True)
    vh_backscatter: Mapped[float | None] = mapped_column(Float, nullable=True)
    vci: Mapped[float] = mapped_column(Float)
    tci: Mapped[float] = mapped_column(Float)
    vhi: Mapped[float] = mapped_column(Float)
    smi: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_level: Mapped[str] = mapped_column(String(20))   # none|mild|moderate|severe
    stress_confidence: Mapped[float] = mapped_column(Float)
