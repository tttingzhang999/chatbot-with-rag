"""
Retrieval service for hybrid search (Semantic + BM25).

This module implements:
- Semantic search using pgvector cosine similarity
- BM25 full-text search using PostgreSQL ts_rank
- Hybrid search with score normalization and weighted merging
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.core.bedrock_client import get_bedrock_client
from src.core.config import settings
from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant document chunks using hybrid search."""

    def __init__(self, db: Session):
        """
        Initialize retrieval service.

        Args:
            db: Database session
        """
        self.db = db
        self.bedrock_client = get_bedrock_client()

    def semantic_search(
        self,
        query_embedding: list[float],
        top_k: int,
        user_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search using vector similarity.

        Args:
            query_embedding: Query embedding vector (1024 dimensions)
            top_k: Number of results to return
            user_id: Optional user ID to filter documents by owner

        Returns:
            List of dicts with chunk info and cosine similarity scores
        """
        try:
            # Build query with vector similarity
            # pgvector uses <=> for cosine distance (lower is better)
            # We convert to similarity: 1 - distance
            query = (
                self.db.query(
                    DocumentChunk.id,
                    DocumentChunk.content,
                    DocumentChunk.chunk_metadata,
                    DocumentChunk.document_id,
                    Document.file_name,
                    # Cosine similarity = 1 - cosine distance
                    (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label(
                        "similarity"
                    ),
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .filter(Document.status == "completed")
            )

            # Filter by user if specified
            if user_id:
                query = query.filter(Document.user_id == user_id)

            # Order by similarity (highest first) and limit
            results = query.order_by(text("similarity DESC")).limit(top_k).all()

            chunks = []
            for row in results:
                chunks.append(
                    {
                        "chunk_id": str(row.id),
                        "content": row.content,
                        "metadata": row.chunk_metadata or {},
                        "document_id": str(row.document_id),
                        "file_name": row.file_name,
                        "score": float(row.similarity),
                        "search_type": "semantic",
                    }
                )

            logger.info(f"Semantic search returned {len(chunks)} results")
            return chunks

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    def bm25_search(
        self,
        query_text: str,
        top_k: int,
        user_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform BM25 full-text search using PostgreSQL ts_rank.

        Args:
            query_text: Search query text
            top_k: Number of results to return
            user_id: Optional user ID to filter documents by owner

        Returns:
            List of dicts with chunk info and BM25 scores
        """
        try:
            # Clean query text for tsquery
            # Remove special characters that could break tsquery
            cleaned_query = query_text.replace("'", "").replace('"', "")

            # Use 'simple' text search config for better Chinese support
            # 'simple' doesn't do stemming, which works better for Chinese text
            # It also handles mixed Chinese-English content better than 'english'
            tsquery = func.plainto_tsquery("simple", cleaned_query)

            # Build query with ts_rank for BM25-style scoring
            query = (
                self.db.query(
                    DocumentChunk.id,
                    DocumentChunk.content,
                    DocumentChunk.chunk_metadata,
                    DocumentChunk.document_id,
                    Document.file_name,
                    # ts_rank scores based on term frequency and document statistics
                    func.ts_rank(
                        DocumentChunk.content_tsvector,
                        tsquery,
                    ).label("rank"),
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .filter(Document.status == "completed")
                .filter(DocumentChunk.content_tsvector.op("@@")(tsquery))
            )

            # Filter by user if specified
            if user_id:
                query = query.filter(Document.user_id == user_id)

            # Order by rank (highest first) and limit
            results = query.order_by(text("rank DESC")).limit(top_k).all()

            chunks = []
            for row in results:
                chunks.append(
                    {
                        "chunk_id": str(row.id),
                        "content": row.content,
                        "metadata": row.chunk_metadata or {},
                        "document_id": str(row.document_id),
                        "file_name": row.file_name,
                        "score": float(row.rank),
                        "search_type": "bm25",
                    }
                )

            logger.info(f"BM25 search returned {len(chunks)} results")
            return chunks

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            raise

    def hybrid_search(
        self,
        query_text: str,
        top_k: int,
        user_id: UUID | None = None,
        semantic_ratio: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining semantic and BM25 results.

        Args:
            query_text: Search query text
            top_k: Total number of results to return
            user_id: Optional user ID to filter documents by owner
            semantic_ratio: Weight for semantic search (0-1). If None, uses config default

        Returns:
            List of dicts with chunk info and combined scores, sorted by score
        """
        try:
            # Use config default if not specified
            semantic_ratio = semantic_ratio or settings.SEMANTIC_SEARCH_RATIO
            bm25_ratio = 1.0 - semantic_ratio

            logger.info(f"Hybrid search: semantic_ratio={semantic_ratio}, bm25_ratio={bm25_ratio}")

            # Generate query embedding for semantic search with throttling handling
            try:
                query_embedding = self.bedrock_client.generate_query_embedding(query_text)
            except Exception as e:
                # If embedding generation fails due to throttling, fall back to BM25 only
                if "ThrottlingException" in str(e) or "Too many requests" in str(e):
                    logger.warning(
                        "Throttling detected during query embedding generation, "
                        "falling back to BM25-only search"
                    )
                    # Fall back to BM25-only search
                    bm25_results = self.bm25_search(query_text, top_k, user_id)
                    return bm25_results
                else:
                    # Re-raise other errors
                    raise

            # Get more results from each search to ensure good coverage
            # We'll retrieve 2x top_k from each and then merge
            retrieve_k = top_k * 2

            # Perform both searches in parallel (conceptually)
            semantic_results = self.semantic_search(query_embedding, retrieve_k, user_id)
            bm25_results = self.bm25_search(query_text, retrieve_k, user_id)

            # Normalize scores for both result sets
            semantic_normalized = self._normalize_scores(semantic_results)
            bm25_normalized = self._normalize_scores(bm25_results)

            # Merge results with weighted scores
            merged_results = self._merge_results(
                semantic_normalized,
                bm25_normalized,
                semantic_ratio,
                bm25_ratio,
            )

            # Sort by combined score and take top_k
            merged_results.sort(key=lambda x: x["score"], reverse=True)
            top_results = merged_results[:top_k]

            # Filter by relevance threshold to avoid returning irrelevant documents
            final_results = [r for r in top_results if r["score"] >= settings.RELEVANCE_THRESHOLD]

            logger.info(
                f"Hybrid search returned {len(final_results)} results "
                f"(from {len(semantic_results)} semantic + {len(bm25_results)} BM25, "
                f"filtered by threshold {settings.RELEVANCE_THRESHOLD})"
            )

            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    def _normalize_scores(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Normalize scores to 0-1 range using min-max normalization.

        Args:
            results: List of search results with scores

        Returns:
            Results with normalized scores
        """
        if not results:
            return results

        scores = [r["score"] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        # Avoid division by zero
        score_range = max_score - min_score
        if score_range == 0:
            # All scores are the same, set normalized to 1.0
            for r in results:
                r["normalized_score"] = 1.0
        else:
            for r in results:
                r["normalized_score"] = (r["score"] - min_score) / score_range

        return results

    def _merge_results(
        self,
        semantic_results: list[dict[str, Any]],
        bm25_results: list[dict[str, Any]],
        semantic_weight: float,
        bm25_weight: float,
    ) -> list[dict[str, Any]]:
        """
        Merge semantic and BM25 results with weighted scores.

        Args:
            semantic_results: Results from semantic search (with normalized scores)
            bm25_results: Results from BM25 search (with normalized scores)
            semantic_weight: Weight for semantic scores
            bm25_weight: Weight for BM25 scores

        Returns:
            Merged results with combined scores
        """
        # Create lookup dictionaries for fast merging
        semantic_lookup = {r["chunk_id"]: r for r in semantic_results}
        bm25_lookup = {r["chunk_id"]: r for r in bm25_results}

        # Get all unique chunk IDs
        all_chunk_ids = set(semantic_lookup.keys()) | set(bm25_lookup.keys())

        merged = []
        for chunk_id in all_chunk_ids:
            semantic_result = semantic_lookup.get(chunk_id)
            bm25_result = bm25_lookup.get(chunk_id)

            # Calculate weighted combined score
            semantic_score = (
                semantic_result.get("normalized_score", 0.0) if semantic_result else 0.0
            )
            bm25_score = bm25_result.get("normalized_score", 0.0) if bm25_result else 0.0

            combined_score = (semantic_weight * semantic_score) + (bm25_weight * bm25_score)

            # Use the result that exists (prefer semantic if both exist)
            base_result = semantic_result or bm25_result

            # Create merged result
            merged_result = {
                "chunk_id": chunk_id,
                "content": base_result["content"],
                "metadata": base_result["metadata"],
                "document_id": base_result["document_id"],
                "file_name": base_result["file_name"],
                "score": combined_score,
                "semantic_score": semantic_score,
                "bm25_score": bm25_score,
                "search_type": "hybrid",
            }

            merged.append(merged_result)

        return merged


def get_retrieval_service(db: Session) -> RetrievalService:
    """
    Factory function to get a RetrievalService instance.

    Args:
        db: Database session

    Returns:
        RetrievalService instance
    """
    return RetrievalService(db)
