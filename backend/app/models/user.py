from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(50), default="viewer") # admin, manager, farmer, viewer
    is_active = Column(Boolean, default=True)
