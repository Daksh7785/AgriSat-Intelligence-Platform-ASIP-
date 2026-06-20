from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False) # auth, classification, stress, advisory
    details = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
