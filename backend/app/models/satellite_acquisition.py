"""Raw satellite acquisition metadata — one row per scene per command area per date."""
from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import String, Float, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SatelliteAcquisition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "satellite_acquisitions"

    satellite: Mapped[str] = mapped_column(String(50))           # 'Sentinel-2', 'EOS-04', 'Sentinel-1', 'NISAR'
    acquisition_date: Mapped[date] = mapped_column(Date)
    command_area_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    cloud_cover_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_path: Mapped[str] = mapped_column(String(500))          # MinIO object path
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
