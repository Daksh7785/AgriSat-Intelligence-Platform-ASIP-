from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Farmer(BaseModel):
    __tablename__ = "farmers"

    name = Column(String(200), nullable=False)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    preferred_language = Column(String(20), default="hi") # hi, en, pa, te, ta
    district = Column(String(100))
    state = Column(String(100))
    aadhaar_hash = Column(String(64), nullable=True)
    whatsapp_opt_in = Column(Boolean, default=False)

    # Relationships
    fields = relationship("Field", back_populates="farmer")
