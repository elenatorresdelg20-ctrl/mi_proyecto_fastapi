import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DEFAULT_SQLITE_URL = "sqlite:///./saas_v1.db"
raw_db_url = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)

SQLALCHEMY_DATABASE_URL = raw_db_url

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_tables():
    """Create all tables registered on the shared Base.

    Importing the models inside this function ensures that metadata is
    populated before attempting to create the tables, preventing silent
    no-op creations when the app starts without prior imports.
    """
    from app import models  # noqa: F401 ensures model modules are registered
    from app.models import models as model_definitions  # noqa: F401

    Base.metadata.create_all(bind=engine)
