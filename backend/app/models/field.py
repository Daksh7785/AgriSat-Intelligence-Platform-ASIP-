"""Individual farm fields — the primary spatial unit for advisory generation."""
from __future__ import annotations
import uuid
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Field(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "fields"

    command_area_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("command_areas.id"))
    farmer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=True)
    geometry = mapped_column(Geometry("POLYGON", srid=4326))
    area_hectares: Mapped[float] = mapped_column(Float)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
