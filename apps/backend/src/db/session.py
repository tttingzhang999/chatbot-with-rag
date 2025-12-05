"""
Database session management.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings

# Disable SQLAlchemy logging to reduce console noise
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Create engine with NullPool for Lambda compatibility
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Disable SQL echo
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
