"""Phenology tracking per field per season."""
from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import String, Float, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PhenologyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "phenology_records"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    crop_type: Mapped[str] = mapped_column(String(100))
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sowing_date_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # optical|sar|optical+sar_agree
    current_stage: Mapped[str] = mapped_column(String(50))
    stage_start_date: Mapped[date] = mapped_column(Date)
    days_since_sowing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gdd_accumulated: Mapped[float] = mapped_column(Float, default=0.0)
