"""Compatibility layer for legacy imports.

This module now re-exports the canonical engine, SessionLocal and Base from
``app.core.db`` to avoid maintaining two divergent database configurations.
Use ``app.core.db`` directly for new code.
"""
from app.core.db import Base, SessionLocal, engine, SQLALCHEMY_DATABASE_URL, create_tables

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "SQLALCHEMY_DATABASE_URL",
    "create_tables",
]
