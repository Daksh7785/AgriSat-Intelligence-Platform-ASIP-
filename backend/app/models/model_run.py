"""Model training/inference run records — drives the validation/accuracy reporting."""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Date, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ModelRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "model_runs"

    run_date: Mapped[date] = mapped_column(Date)
    command_area_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    model_name: Mapped[str] = mapped_column(String(100))     # 'crop_classifier', 'phenology_lstm', etc.
    model_version: Mapped[str] = mapped_column(String(50))
    overall_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    kappa_coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1_per_class: Mapped[dict] = mapped_column(JSON, default=dict)
    confusion_matrix: Mapped[list] = mapped_column(JSON, default=list)
    n_validation_samples: Mapped[int] = mapped_column(Integer, default=0)
    ground_truth_is_synthetic: Mapped[bool] = mapped_column(default=False)
    synthetic_fraction: Mapped[float] = mapped_column(Float, default=0.0)
    processing_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")


class ActiveLearningQueueEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "active_learning_queue"

    from sqlalchemy import ForeignKey  # local import to keep file self-contained for copy-paste

    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), unique=True)
    reason: Mapped[str] = mapped_column(String(200))
    queued_at: Mapped[datetime | None] = mapped_column(default=None)
