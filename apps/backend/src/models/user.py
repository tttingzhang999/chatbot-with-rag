"""
User model for authentication.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.base import Base


class User(Base):
    """
    Represents a user account.

    Stores user credentials and profile information.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Conversation.user_id",
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_is_active", "is_active"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
