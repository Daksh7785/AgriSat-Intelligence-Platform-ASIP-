"""Append-only audit log — covers auth events, advisory delivery, and insurance evidence."""
from __future__ import annotations
import uuid
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    event_type: Mapped[str] = mapped_column(String(100))     # 'login', 'advisory_delivered', 'insurance_evidence_generated'
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)   # user email or 'system'
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class InsuranceEvidenceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Hashed, timestamped evidence bundle backing a loss estimate — see Feature 9
    from the innovation prompt. Auditable without a blockchain dependency."""
    __tablename__ = "insurance_evidence_records"

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"))
    estimated_loss_pct: Mapped[float] = mapped_column(default=0.0)
    confidence: Mapped[str] = mapped_column(String(20))
    stage_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_hash: Mapped[str] = mapped_column(String(64))
    evidence_payload: Mapped[dict] = mapped_column(JSON, default=dict)
