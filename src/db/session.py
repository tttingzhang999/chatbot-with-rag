"""
Database session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings

# Create engine with NullPool for Lambda compatibility
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Database session dependency for FastAPI.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
