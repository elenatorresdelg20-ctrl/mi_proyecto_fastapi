from sqlalchemy import Column, Integer, Float, DateTime, String, Index
from app.core.database import Base

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("idx_tenant_date", "tenant_id", "date"),)
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    product = Column(String)
    amount = Column(Float)
    channel = Column(String, default="Upload")
    cost = Column(Float, nullable=True)
