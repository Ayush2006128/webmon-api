import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

def get_db():
    """Dependency that provides a database session for a request.

    Yields a SQLAlchemy SessionLocal instance and ensures that the session
    is properly closed after the request is finished.

    Raises:
        Exception: If the DATABASE_URL environment variable is not configured.
    """
    if not SessionLocal:
        raise Exception("DATABASE_URL is not set.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
