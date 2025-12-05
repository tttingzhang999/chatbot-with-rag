"""
Database initialization script.

This script:
1. Creates the pgvector extension
2. Creates all tables defined in the models
"""

from sqlalchemy import text

from src.db.base import Base
from src.db.session import engine

# Import all models to ensure they are registered with Base
from src.models import Conversation, Document, DocumentChunk, Message, User  # noqa: F401


def init_db() -> None:
    """
    Initialize the database.

    - Creates the pgvector extension if it doesn't exist
    - Creates all tables defined in the SQLAlchemy models
    """
    with engine.begin() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Enable pg_trgm extension for better text search
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")
    print("Created tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_db()
