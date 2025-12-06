from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    api_key = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)
