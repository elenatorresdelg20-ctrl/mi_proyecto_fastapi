"""Tenant model re-exported from the consolidated models module.

This keeps backward compatibility for legacy imports while ensuring all
entities share the same SQLAlchemy Base and metadata.
"""
from app.models.models import Tenant

__all__ = ["Tenant"]
