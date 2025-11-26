"""
Document processing service for RAG system.

Handles document upload, text extraction, chunking, embedding generation,
and BM25 index creation for hybrid search.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Main document processing service.

    Orchestrates the complete pipeline: extract → chunk → embed → store
    """

    def __init__(self, db: Session):
        """Initialize processor with database session."""
        self.db = db
        self.chunk_size = 512  # Default chunk size in characters
        self.chunk_overlap = 128  # Default overlap size

    def process_document_sync(
        self,
        document_id: UUID,
        file_path: str,
        file_type: str,
    ) -> dict[str, Any]:
        """
        Process document synchronously (simulates Lambda trigger).

        Args:
            document_id: UUID of the document record
            file_path: Path to the uploaded file
            file_type: File type (pdf, docx, txt)

        Returns:
            dict with processing results
        """
        try:
            logger.info(f"Starting document processing: {document_id}")

            # Update document status to processing
            self._update_document_status(document_id, "processing")

            # Step 1: Extract text
            text = self.extract_text(file_path, file_type)
            if not text or not text.strip():
                raise ValueError("No text content extracted from document")

            # Step 2: Chunk text
            chunks = self.chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from document {document_id}")

            # Step 3: Generate embeddings for all chunks
            embeddings = self.generate_embeddings(chunks)

            # Step 4: Create BM25 indexes
            bm25_vectors = self.create_bm25_indexes(chunks)

            # Step 5: Save chunks to database
            self.save_chunks_to_db(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                bm25_vectors=bm25_vectors,
            )

            # Update document status to completed
            self._update_document_status(document_id, "completed")

            logger.info(f"Document processing completed: {document_id}")
            return {
                "status": "success",
                "document_id": str(document_id),
                "chunks_created": len(chunks),
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            self._update_document_status(
                document_id,
                "failed",
                error_message=str(e),
            )
            return {
                "status": "failed",
                "document_id": str(document_id),
                "error": str(e),
            }

    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from document.

        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, docx, txt)

        Returns:
            Extracted text content

        Note:
            This is a placeholder implementation. For production:
            - PDF: Use pypdf, PyMuPDF, or pdfplumber
            - DOCX: Use python-docx
            - TXT: Direct read with encoding detection
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = file_type.lower()

        if file_type == "txt":
            # Read text file directly
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif file_type == "pdf":
            # TODO: Implement PDF extraction
            # Recommended: pypdf or PyMuPDF (fitz)
            # Example:
            # from pypdf import PdfReader
            # reader = PdfReader(file_path)
            # text = "\n".join([page.extract_text() for page in reader.pages])
            logger.warning("PDF extraction not yet implemented, returning placeholder")
            return f"[PDF content placeholder from {Path(file_path).name}]\n\nThis is sample text content that would be extracted from the PDF file. In production, this will be replaced with actual text extraction using pypdf or PyMuPDF library."

        elif file_type in ["docx", "doc"]:
            # TODO: Implement DOCX extraction
            # Recommended: python-docx
            # Example:
            # from docx import Document
            # doc = Document(file_path)
            # text = "\n".join([para.text for para in doc.paragraphs])
            logger.warning("DOCX extraction not yet implemented, returning placeholder")
            return f"[DOCX content placeholder from {Path(file_path).name}]\n\nThis is sample text content that would be extracted from the DOCX file. In production, this will be replaced with actual text extraction using python-docx library."

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_text(
        self,
        text: str,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters (default: 512)
            overlap: Overlap size in characters (default: 128)

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        if chunk_size <= overlap:
            raise ValueError("Chunk size must be greater than overlap")

        # Clean text: normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk from start to start + chunk_size
            end = start + chunk_size

            # If not the last chunk, try to break at sentence/word boundary
            if end < len(text):
                # Look for sentence boundary (. ! ?)
                sentence_end = text.rfind(".", start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind("!", start, end)
                if sentence_end == -1:
                    sentence_end = text.rfind("?", start, end)

                # If no sentence boundary, look for word boundary
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Find last space
                    space_pos = text.rfind(" ", start, end)
                    if space_pos > start:
                        end = space_pos

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position forward with overlap
            start = end - overlap if end < len(text) else len(text)

        return chunks

    def generate_embeddings(self, chunks: list[str]) -> list[list[float]]:
        """
        Generate embeddings for text chunks using Cohere Embed v4.

        Args:
            chunks: List of text chunks

        Returns:
            List of embedding vectors (1024 dimensions each)

        Note:
            This is a placeholder. For production, use:
            - Amazon Bedrock with Cohere Embed v4
            - Model ID: cohere.embed-english-v3 or cohere.embed-multilingual-v3
        """
        # TODO: Implement Bedrock embedding generation
        # Example using boto3:
        # import boto3
        # bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        # response = bedrock.invoke_model(
        #     modelId='cohere.embed-english-v3',
        #     body=json.dumps({
        #         'texts': chunks,
        #         'input_type': 'search_document',
        #         'embedding_types': ['float']
        #     })
        # )

        logger.warning("Bedrock embedding generation not yet implemented, using mock")

        # Return mock embeddings (1024 dimensions, all zeros)
        # In production, this will return actual embeddings from Cohere
        return [[0.0] * 1024 for _ in chunks]

    def create_bm25_indexes(self, chunks: list[str]) -> list[str]:
        """
        Create BM25 full-text search indexes for chunks.

        Args:
            chunks: List of text chunks

        Returns:
            List of tsvector strings for PostgreSQL

        Note:
            PostgreSQL's to_tsvector() will be used in the database insert.
            This method prepares the text for indexing.
        """
        # Clean and prepare text for BM25 indexing
        # PostgreSQL's to_tsvector will handle the actual TSVECTOR creation
        processed_chunks = []

        for chunk in chunks:
            # Basic text cleaning for BM25
            # Remove special characters, normalize whitespace
            cleaned = re.sub(r"[^\w\s]", " ", chunk)
            cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
            processed_chunks.append(cleaned)

        return processed_chunks

    def save_chunks_to_db(
        self,
        document_id: UUID,
        chunks: list[str],
        embeddings: list[list[float]],
        bm25_vectors: list[str],
    ) -> None:
        """
        Save document chunks with embeddings and BM25 data to database.

        Args:
            document_id: UUID of the parent document
            chunks: List of text chunks
            embeddings: List of embedding vectors
            bm25_vectors: List of processed text for BM25
        """
        if not (len(chunks) == len(embeddings) == len(bm25_vectors)):
            raise ValueError("Chunks, embeddings, and BM25 vectors must have same length")

        try:
            # Create DocumentChunk objects
            chunk_objects = []
            for idx, (chunk_text, embedding, bm25_text) in enumerate(
                zip(chunks, embeddings, bm25_vectors, strict=True)
            ):
                chunk_obj = DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    content=chunk_text,
                    embedding=embedding,
                    # Note: content_tsvector will be set by database trigger
                    # or we can use raw SQL: func.to_tsvector('english', chunk_text)
                    chunk_metadata={
                        "char_count": len(chunk_text),
                        "word_count": len(chunk_text.split()),
                    },
                )
                chunk_objects.append(chunk_obj)

            # Bulk insert chunks
            self.db.add_all(chunk_objects)
            self.db.commit()

            logger.info(f"Saved {len(chunk_objects)} chunks for document {document_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving chunks to database: {e}")
            raise

    def _update_document_status(
        self,
        document_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        Update document processing status.

        Args:
            document_id: Document UUID
            status: Status value (processing, completed, failed)
            error_message: Error message if status is failed
        """
        try:
            # Update document status
            update_values = {"status": status}
            if error_message is not None:
                update_values["error_message"] = error_message

            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(**update_values)
            )
            self.db.execute(stmt)
            self.db.commit()

            logger.info(f"Updated document {document_id} status to: {status}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating document status: {e}")
            # Don't raise here to avoid masking original errors


def get_user_documents(db: Session, user_id: UUID) -> list[dict[str, Any]]:
    """
    Get all documents uploaded by a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        List of document metadata dictionaries
    """
    stmt = (
        select(
            Document.id,
            Document.file_name,
            Document.file_type,
            Document.file_size,
            Document.upload_date,
            Document.status,
            Document.error_message,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .where(Document.user_id == user_id)
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .group_by(
            Document.id,
            Document.file_name,
            Document.file_type,
            Document.file_size,
            Document.upload_date,
            Document.status,
            Document.error_message,
        )
        .order_by(Document.upload_date.desc())
    )

    result = db.execute(stmt)
    rows = result.all()

    documents = []
    for row in rows:
        documents.append(
            {
                "id": str(row.id),
                "file_name": row.file_name,
                "file_type": row.file_type,
                "file_size": row.file_size,
                "upload_date": row.upload_date.isoformat(),
                "status": row.status,
                "error_message": row.error_message,
                "chunk_count": row.chunk_count,
            }
        )

    return documents


def delete_document(db: Session, document_id: UUID, user_id: UUID) -> bool:
    """
    Delete a document and all its chunks.

    Args:
        db: Database session
        document_id: Document UUID
        user_id: User UUID (for authorization)

    Returns:
        True if deleted successfully, False if not found
    """
    try:
        # Check if document exists and belongs to user
        stmt = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        # Delete associated file if it exists
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                logger.info(f"Deleted file: {document.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {document.file_path}: {e}")

        # Delete document (cascades to chunks)
        stmt = delete(Document).where(Document.id == document_id)
        db.execute(stmt)
        db.commit()

        logger.info(f"Deleted document {document_id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document {document_id}: {e}")
        raise
