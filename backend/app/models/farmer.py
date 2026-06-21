"""Farmer records — phone-first identity, no PII beyond what delivery requires."""
from __future__ import annotations
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Farmer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "farmers"

    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(15), index=True)
    preferred_language: Mapped[str] = mapped_column(String(20), default="hi")
    district: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    aadhaar_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # hashed, never plain
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
