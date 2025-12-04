from app.core.database import Base, SessionLocal, engine


def create_tables():
    Base.metadata.create_all(bind=engine)
