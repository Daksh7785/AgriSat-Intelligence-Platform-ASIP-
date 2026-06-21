"""Farmer/officer feedback on delivered advisories — feeds the active learning queue."""
from __future__ import annotations
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdvisoryFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "advisory_feedback"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    advisory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("irrigation_advisories.id"))
    feedback_type: Mapped[str] = mapped_column(String(50))   # followed|not_followed|outcome_seemed_wrong|crop_correction
    submitted_by_role: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_crop_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
