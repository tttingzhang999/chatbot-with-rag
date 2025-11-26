"""
File upload routes with document processing.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.api.deps import CurrentUser, DBSession
from src.models.document import Document
from src.services.document_service import DocumentProcessor, delete_document, get_user_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Upload directory (for local development)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class UploadResponse(BaseModel):
    """Upload response model."""

    document_id: str
    filename: str
    size: int
    content_type: str
    message: str


class DocumentListItem(BaseModel):
    """Document list item model."""

    id: str
    file_name: str
    file_type: str
    file_size: int
    upload_date: str
    status: str
    error_message: str | None
    chunk_count: int


class DocumentListResponse(BaseModel):
    """Document list response model."""

    documents: list[DocumentListItem]
    total: int


class DeleteResponse(BaseModel):
    """Delete response model."""

    message: str


def process_document_background(
    document_id: uuid.UUID,
    file_path: str,
    file_type: str,
    db_url: str,
) -> None:
    """
    Background task to process document.

    This simulates AWS Lambda async processing.

    Args:
        document_id: Document UUID
        file_path: Path to uploaded file
        file_type: File type (pdf, docx, txt)
        db_url: Database URL for creating new session
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    try:
        logger.info(f"Background processing started for document: {document_id}")

        # Create new database session for background task
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Create processor and process document
            processor = DocumentProcessor(db)
            result = processor.process_document_sync(document_id, file_path, file_type)
            logger.info(f"Document processed: {result}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")


@router.post("/document", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> UploadResponse:
    """
    Upload a document and trigger processing.

    This endpoint:
    1. Saves file to local storage (or S3 in production)
    2. Creates Document record in database
    3. Triggers async processing (simulates Lambda)

    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded file
        current_user: Current authenticated user
        db: Database session

    Returns:
        UploadResponse: Upload confirmation with document ID
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Get file extension
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in ["pdf", "txt", "docx", "doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported: pdf, txt, docx",
        )

    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Generate unique filename
        document_id = uuid.uuid4()
        unique_filename = f"{document_id}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file to local storage
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {file_path}")

        # Create Document record in database
        document = Document(
            id=document_id,
            user_id=current_user.id,
            file_name=file.filename,
            file_path=str(file_path),
            file_type=file_ext,
            file_size=file_size,
            status="pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Document record created: {document_id}")

        # Trigger background processing (simulates Lambda)
        from src.core.config import settings

        background_tasks.add_task(
            process_document_background,
            document_id=document_id,
            file_path=str(file_path),
            file_type=file_ext,
            db_url=settings.DATABASE_URL,
        )

        return UploadResponse(
            document_id=str(document_id),
            filename=file.filename,
            size=file_size,
            content_type=file.content_type or "application/octet-stream",
            message="File uploaded successfully. Processing started in background.",
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> DocumentListResponse:
    """
    Get all documents uploaded by current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        DocumentListResponse: List of documents
    """
    try:
        documents = get_user_documents(db, current_user.id)

        return DocumentListResponse(
            documents=[DocumentListItem(**doc) for doc in documents],
            total=len(documents),
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document_endpoint(
    document_id: str,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> DeleteResponse:
    """
    Delete a document and all its chunks.

    Args:
        document_id: Document UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DeleteResponse: Deletion confirmation
    """
    try:
        # Validate UUID
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format",
            )

        # Delete document
        deleted = delete_document(db, doc_uuid, current_user.id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized",
            )

        return DeleteResponse(message="Document deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
