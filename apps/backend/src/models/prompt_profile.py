"""
PromptProfile model for configurable RAG chatbot settings.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from src.db.base import Base


class PromptProfile(Base):
    """
    Represents a user's prompt profile configuration.

    Each profile contains prompts, RAG settings, and LLM configuration.
    Users can have multiple profiles with isolated conversations and documents.
    """

    __tablename__ = "prompt_profiles"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)

    # Prompt Templates
    system_prompt = Column(Text, nullable=False)
    rag_system_prompt_template = Column(Text, nullable=False)

    # RAG Configuration
    chunk_size = Column(Integer, default=512, nullable=False)
    chunk_overlap = Column(Integer, default=128, nullable=False)
    top_k_chunks = Column(Integer, default=10, nullable=False)
    semantic_search_ratio = Column(Float, default=0.5, nullable=False)
    relevance_threshold = Column(Float, default=0.3, nullable=False)

    # LLM Configuration
    llm_model_id = Column(String(100), default="amazon.nova-lite-v1:0", nullable=False)
    llm_temperature = Column(Float, default=0.7, nullable=False)
    llm_top_p = Column(Float, default=0.9, nullable=False)
    llm_max_tokens = Column(Integer, default=2048, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="prompt_profiles")
    conversations = relationship(
        "Conversation",
        back_populates="profile",
        cascade="all, delete-orphan",
        foreign_keys="Conversation.profile_id",
    )
    documents = relationship(
        "Document",
        back_populates="profile",
        cascade="all, delete-orphan",
        foreign_keys="Document.profile_id",
    )

    # Constraints and Indexes
    __table_args__ = (
        # Unique constraint: user can't have duplicate profile names
        Index("idx_profile_user_name", "user_id", "name", unique=True),
        # Index for querying user's profiles
        Index("idx_profile_user_id", "user_id"),
        # Index for finding default profiles
        Index("idx_profile_is_default", "is_default"),
        # Compound index for finding user's default profile
        Index("idx_profile_user_default", "user_id", "is_default"),
        # Check constraints for valid ranges
        CheckConstraint("chunk_size >= 100 AND chunk_size <= 2000", name="check_chunk_size_range"),
        CheckConstraint(
            "chunk_overlap >= 0 AND chunk_overlap <= 500", name="check_chunk_overlap_range"
        ),
        CheckConstraint("chunk_overlap < chunk_size", name="check_chunk_overlap_less_than_size"),
        CheckConstraint("top_k_chunks >= 1 AND top_k_chunks <= 50", name="check_top_k_range"),
        CheckConstraint(
            "semantic_search_ratio >= 0.0 AND semantic_search_ratio <= 1.0",
            name="check_semantic_ratio_range",
        ),
        CheckConstraint(
            "relevance_threshold >= 0.0 AND relevance_threshold <= 1.0",
            name="check_relevance_threshold_range",
        ),
        CheckConstraint(
            "llm_temperature >= 0.0 AND llm_temperature <= 1.0", name="check_temperature_range"
        ),
        CheckConstraint("llm_top_p >= 0.0 AND llm_top_p <= 1.0", name="check_top_p_range"),
        CheckConstraint(
            "llm_max_tokens >= 256 AND llm_max_tokens <= 4096", name="check_max_tokens_range"
        ),
    )

    @validates("rag_system_prompt_template")
    def validate_rag_template(self, _, value):
        """Validate that RAG template contains {context} placeholder."""
        if "{context}" not in value:
            raise ValueError("rag_system_prompt_template must contain {context} placeholder")
        return value

    def __repr__(self):
        return f"<PromptProfile(id={self.id}, name='{self.name}', user_id={self.user_id}, is_default={self.is_default})>"
