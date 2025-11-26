"""
Document and DocumentChunk models for RAG system.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import relationship

from src.db.base import Base


class Document(Base):
    """
    Represents an uploaded document.

    Stores metadata about the original document uploaded to S3.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # S3 path
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    file_size = Column(Integer)  # bytes
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # Error details if status is failed
    extra_metadata = Column(JSONB, default={})  # Additional flexible metadata

    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Document(id={self.id}, file_name='{self.file_name}')>"


class DocumentChunk(Base):
    """
    Represents a chunk of a document with its embedding and BM25 data.

    Stores the actual text content, vector embedding, and full-text search data
    for efficient hybrid search (semantic + BM25).
    """

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)  # Actual text content

    # Vector embedding for semantic search (Cohere Embed v4: 1024 dimensions)
    embedding = Column(Vector(1024))

    # Full-text search vector for BM25/TFIDF search
    content_tsvector = Column(TSVECTOR)

    # Metadata about the chunk
    chunk_metadata = Column(
        JSONB,
        default={},
    )  # e.g., {"start_char": 0, "end_char": 1000, "page": 1}

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes for efficient searching
    __table_args__ = (
        # Index for vector similarity search (cosine distance)
        Index(
            "idx_embedding_vector",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # Index for full-text search
        Index("idx_content_tsvector", content_tsvector, postgresql_using="gin"),
        # Index for document_id + chunk_index lookup
        Index("idx_document_chunk", "document_id", "chunk_index"),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
