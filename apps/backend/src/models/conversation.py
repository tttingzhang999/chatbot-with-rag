"""
Conversation and Message models for multi-turn chat.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.db.base import Base


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    Represents a conversation session.

    Groups multiple messages together as part of a single conversation flow.
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=True)  # Optional conversation title
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    extra_metadata = Column(JSONB, default={})  # Additional flexible metadata

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    # Indexes
    __table_args__ = (
        Index("idx_conversation_user_id", "user_id"),
        Index("idx_conversation_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id='{self.user_id}')>"


class Message(Base):
    """
    Represents a single message in a conversation.

    Stores user questions and assistant responses, along with retrieved context chunks.
    """

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Store which chunks were retrieved for this message (for assistant messages)
    retrieved_chunks = Column(
        JSONB,
        default=[],
    )  # List of chunk IDs or chunk data

    # Store retrieval scores and metadata
    retrieval_metadata = Column(
        JSONB,
        default={},
    )  # e.g., {"semantic_scores": [...], "bm25_scores": [...]}

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_message_conversation_id", "conversation_id"),
        Index("idx_message_created_at", "created_at"),
        Index("idx_message_role", "role"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"
