"""8-day irrigation advisory per field."""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import String, Float, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IrrigationAdvisory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "irrigation_advisories"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    advisory_date: Mapped[date] = mapped_column(Date)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date] = mapped_column(Date)
    etc_mm: Mapped[float] = mapped_column(Float)
    eta_mm: Mapped[float] = mapped_column(Float)
    eta_source: Mapped[str] = mapped_column(String(20), default="sebal")  # 'sebal' | 'mod16_fallback'
    effective_rainfall_mm: Mapped[float] = mapped_column(Float)
    forecast_rain_mm_3day: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_deficit_mm: Mapped[float] = mapped_column(Float)
    irrigation_requirement_mm: Mapped[float] = mapped_column(Float)
    advisory_class: Mapped[str] = mapped_column(String(20))   # none|light|moderate|critical
    advisory_text_en: Mapped[str] = mapped_column(Text)
    advisory_text_hi: Mapped[str] = mapped_column(Text)
    delivered_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CommandAreaAdvisorySummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Aggregated 8-day advisory rollup at the command-area level for the dashboard map."""
    __tablename__ = "command_area_advisory_summaries"

    command_area_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("command_areas.id"))
    summary_date: Mapped[date] = mapped_column(Date)
    n_fields_none: Mapped[int] = mapped_column(default=0)
    n_fields_light: Mapped[int] = mapped_column(default=0)
    n_fields_moderate: Mapped[int] = mapped_column(default=0)
    n_fields_critical: Mapped[int] = mapped_column(default=0)
    total_irrigation_requirement_liters: Mapped[float] = mapped_column(Float, default=0.0)
