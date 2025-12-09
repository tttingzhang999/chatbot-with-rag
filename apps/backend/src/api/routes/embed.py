"""
Embed and chunk management routes.

This module provides endpoints for browsing embedded chunks.
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DBSession
from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeds", tags=["embeds"])


# ========== Request/Response Models ==========


class ChunkListItem(BaseModel):
    """Chunk list item model."""

    id: str
    document_id: str
    chunk_index: int
    content: str
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding_dimension: int | None = None


class ChunkListResponse(BaseModel):
    """Chunk list response model."""

    chunks: list[ChunkListItem]
    total: int
    document_id: str
    document_name: str


# ========== Helper Functions ==========


def get_document_with_ownership(db: Session, document_id: str, user_id: uuid.UUID) -> Document:
    """
    Get document and verify ownership.

    Args:
        db: Database session
        document_id: Document UUID string
        user_id: User UUID

    Returns:
        Document: Document object

    Raises:
        HTTPException: If document not found or user doesn't own it
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format",
        )

    stmt = select(Document).where(Document.id == doc_uuid, Document.user_id == user_id)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )

    return document


# ========== Routes ==========


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
def list_chunks(
    document_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> ChunkListResponse:
    """
    Get all chunks for a document.

    Args:
        document_id: Document UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChunkListResponse: List of chunks
    """
    try:
        document = get_document_with_ownership(db, document_id, current_user.id)

        # Get all chunks for this document
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = db.execute(stmt)
        chunks = result.scalars().all()

        chunk_items = []
        for chunk in chunks:
            embedding_dim = None
            if chunk.embedding is not None:
                # Get embedding dimension from the vector
                embedding_dim = (
                    len(chunk.embedding) if hasattr(chunk.embedding, "__len__") else None
                )

            chunk_items.append(
                ChunkListItem(
                    id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    created_at=chunk.created_at.isoformat(),
                    metadata=chunk.chunk_metadata or {},
                    embedding_dimension=embedding_dim,
                )
            )

        return ChunkListResponse(
            chunks=chunk_items,
            total=len(chunk_items),
            document_id=str(document.id),
            document_name=document.file_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chunks: {str(e)}",
        )
