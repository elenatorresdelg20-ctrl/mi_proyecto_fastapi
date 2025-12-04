from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from ..core.db import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_tenant_admin = Column(Boolean, default=False)


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)


class UserPermission(Base):
    __tablename__ = "user_permissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)
    __table_args__ = (UniqueConstraint("user_id", "permission_id", name="uix_user_permission"),)


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("idx_tenant_date", "tenant_id", "date"),)
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    product = Column(String)
    amount = Column(Float)
    channel = Column(String, default="Upload")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    text = Column(String)
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    is_corrected = Column(Boolean, default=False)


class ExternalIntegration(Base):
    __tablename__ = "external_integrations"
    __table_args__ = (Index("idx_tenant_provider", "tenant_id", "provider"),)
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    provider = Column(String, index=True)
    name = Column(String, nullable=False)
    auth_type = Column(String, nullable=False)
    api_key = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    extra_config = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
