"""
Embed and chunk management routes.

This module provides endpoints for:
1. Browsing, editing, and removing embedded chunks
2. Real-time adjustment of embed model parameters
3. Re-embedding chunks with new parameters
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.api.deps import CurrentUser, DBSession
from src.core.bedrock_client import get_bedrock_client
from src.core.config import settings
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


class ChunkDetailResponse(BaseModel):
    """Chunk detail response model."""

    id: str
    document_id: str
    chunk_index: int
    content: str
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding_dimension: int | None = None
    has_embedding: bool


class UpdateChunkRequest(BaseModel):
    """Request model for updating chunk content."""

    content: str = Field(..., min_length=1, description="New chunk content")


class UpdateChunkResponse(BaseModel):
    """Response model for chunk update."""

    id: str
    content: str
    message: str


class ReEmbedRequest(BaseModel):
    """Request model for re-embedding chunks."""

    input_type: str = Field(
        default="search_document",
        description="Input type for embedding (search_document or search_query)",
    )


class ReEmbedResponse(BaseModel):
    """Response model for re-embedding."""

    chunk_id: str
    message: str
    embedding_dimension: int


class EmbedConfigResponse(BaseModel):
    """Response model for embed configuration."""

    embedding_model_id: str
    embedding_dimension: int
    input_type: str = Field(default="search_document")
    batch_size: int = Field(default=96)


class UpdateEmbedConfigRequest(BaseModel):
    """Request model for updating embed configuration."""

    input_type: str | None = Field(
        default=None,
        description="Input type for embedding (search_document or search_query)",
    )
    batch_size: int | None = Field(
        default=None, ge=1, le=96, description="Batch size for embedding generation"
    )


class DeleteResponse(BaseModel):
    """Delete response model."""

    message: str


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


def get_chunk_with_ownership(db: Session, chunk_id: str, user_id: uuid.UUID) -> DocumentChunk:
    """
    Get chunk and verify document ownership.

    Args:
        db: Database session
        chunk_id: Chunk UUID string
        user_id: User UUID

    Returns:
        DocumentChunk: Chunk object

    Raises:
        HTTPException: If chunk not found or user doesn't own the document
    """
    try:
        chunk_uuid = uuid.UUID(chunk_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chunk ID format",
        )

    stmt = (
        select(DocumentChunk)
        .join(Document)
        .where(DocumentChunk.id == chunk_uuid, Document.user_id == user_id)
    )
    result = db.execute(stmt)
    chunk = result.scalar_one_or_none()

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found or access denied",
        )

    return chunk


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


@router.get("/chunks/{chunk_id}", response_model=ChunkDetailResponse)
def get_chunk(
    chunk_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> ChunkDetailResponse:
    """
    Get chunk details.

    Args:
        chunk_id: Chunk UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChunkDetailResponse: Chunk details
    """
    try:
        chunk = get_chunk_with_ownership(db, chunk_id, current_user.id)

        embedding_dim = None
        has_embedding = False
        if chunk.embedding is not None:
            has_embedding = True
            embedding_dim = len(chunk.embedding) if hasattr(chunk.embedding, "__len__") else None

        return ChunkDetailResponse(
            id=str(chunk.id),
            document_id=str(chunk.document_id),
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            created_at=chunk.created_at.isoformat(),
            metadata=chunk.chunk_metadata or {},
            embedding_dimension=embedding_dim,
            has_embedding=has_embedding,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunk: {str(e)}",
        )


@router.put("/chunks/{chunk_id}", response_model=UpdateChunkResponse)
def update_chunk(
    chunk_id: str,
    request: UpdateChunkRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> UpdateChunkResponse:
    """
    Update chunk content.

    Args:
        chunk_id: Chunk UUID
        request: Update request with new content
        current_user: Current authenticated user
        db: Database session

    Returns:
        UpdateChunkResponse: Update confirmation
    """
    try:
        chunk = get_chunk_with_ownership(db, chunk_id, current_user.id)

        # Update content
        chunk.content = request.content

        # Update metadata
        if chunk.chunk_metadata is None:
            chunk.chunk_metadata = {}
        chunk.chunk_metadata["char_count"] = len(request.content)
        chunk.chunk_metadata["word_count"] = len(request.content.split())

        # Update tsvector for full-text search
        db.execute(
            text(
                "UPDATE document_chunks SET content_tsvector = to_tsvector('simple', :content) WHERE id = :id"
            ),
            {"content": request.content, "id": chunk.id},
        )

        db.commit()

        logger.info(f"Updated chunk {chunk_id}")

        return UpdateChunkResponse(
            id=str(chunk.id),
            content=chunk.content,
            message="Chunk updated successfully. Note: Embedding is not automatically regenerated.",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chunk: {str(e)}",
        )


@router.delete("/chunks/{chunk_id}", response_model=DeleteResponse)
def delete_chunk(
    chunk_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> DeleteResponse:
    """
    Delete a chunk.

    Args:
        chunk_id: Chunk UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DeleteResponse: Deletion confirmation
    """
    try:
        chunk = get_chunk_with_ownership(db, chunk_id, current_user.id)

        db.delete(chunk)
        db.commit()

        logger.info(f"Deleted chunk {chunk_id}")

        return DeleteResponse(message="Chunk deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chunk: {str(e)}",
        )


@router.post("/chunks/{chunk_id}/re-embed", response_model=ReEmbedResponse)
def re_embed_chunk(
    chunk_id: str,
    request: ReEmbedRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> ReEmbedResponse:
    """
    Re-embed a chunk with new parameters.

    Args:
        chunk_id: Chunk UUID
        request: Re-embed request with parameters
        current_user: Current authenticated user
        db: Database session

    Returns:
        ReEmbedResponse: Re-embedding confirmation
    """
    try:
        chunk = get_chunk_with_ownership(db, chunk_id, current_user.id)

        # Generate new embedding
        bedrock_client = get_bedrock_client()
        embeddings = bedrock_client.generate_embeddings(
            [chunk.content], input_type=request.input_type, batch_size=1
        )

        if not embeddings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embedding",
            )

        new_embedding = embeddings[0]

        # Update chunk with new embedding
        chunk.embedding = new_embedding
        db.commit()

        logger.info(f"Re-embedded chunk {chunk_id} with input_type={request.input_type}")

        return ReEmbedResponse(
            chunk_id=str(chunk.id),
            message="Chunk re-embedded successfully",
            embedding_dimension=len(new_embedding),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to re-embed chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-embed chunk: {str(e)}",
        )


@router.post("/documents/{document_id}/re-embed-all", response_model=dict)
def re_embed_all_chunks(
    document_id: str,
    request: ReEmbedRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> dict:
    """
    Re-embed all chunks for a document.

    Args:
        document_id: Document UUID
        request: Re-embed request with parameters
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Re-embedding summary
    """
    try:
        document = get_document_with_ownership(db, document_id, current_user.id)

        # Get all chunks
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = db.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            return {
                "message": "No chunks found for this document",
                "total_chunks": 0,
                "re_embedded": 0,
            }

        # Generate embeddings for all chunks
        bedrock_client = get_bedrock_client()
        texts = [chunk.content for chunk in chunks]
        embeddings = bedrock_client.generate_embeddings(texts, input_type=request.input_type)

        if len(embeddings) != len(chunks):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}",
            )

        # Update all chunks
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk.embedding = embedding

        db.commit()

        logger.info(
            f"Re-embedded {len(chunks)} chunks for document {document_id} "
            f"with input_type={request.input_type}"
        )

        return {
            "message": f"Successfully re-embedded {len(chunks)} chunks",
            "total_chunks": len(chunks),
            "re_embedded": len(chunks),
            "embedding_dimension": len(embeddings[0]) if embeddings else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to re-embed all chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-embed all chunks: {str(e)}",
        )


@router.get("/config", response_model=EmbedConfigResponse)
def get_embed_config() -> EmbedConfigResponse:
    """
    Get current embed model configuration.

    Returns:
        EmbedConfigResponse: Current configuration
    """
    return EmbedConfigResponse(
        embedding_model_id=settings.EMBEDDING_MODEL_ID,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        input_type="search_document",
        batch_size=96,
    )


@router.put("/config", response_model=EmbedConfigResponse)
def update_embed_config(
    request: UpdateEmbedConfigRequest,
) -> EmbedConfigResponse:
    """
    Update embed model configuration (for real-time tuning).

    Note: This endpoint returns the updated config but doesn't persist it.
    The actual embedding generation will use these parameters when provided.

    Returns:
        EmbedConfigResponse: Updated configuration
    """
    # Note: We're not persisting these changes to settings as they're runtime parameters
    # The actual embedding generation will use the provided parameters
    return EmbedConfigResponse(
        embedding_model_id=settings.EMBEDDING_MODEL_ID,
        embedding_dimension=settings.EMBEDDING_DIMENSION,
        input_type=request.input_type or "search_document",
        batch_size=request.batch_size or 96,
    )
