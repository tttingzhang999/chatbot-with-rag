"""
File upload routes with pre-signed URL support.

This module provides endpoints for:
1. Generating pre-signed S3 URLs for direct client-to-S3 uploads
2. Triggering document processing after S3 upload completes
3. Managing documents (list, delete)
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from src.api.deps import CurrentUser, DBSession
from src.core.config import settings
from src.models.document import Document
from src.services.document_service import DocumentProcessor, delete_document, get_user_documents
from src.services.s3_service import get_s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


# ========== Request/Response Models ==========


class PresignedUrlRequest(BaseModel):
    """Request model for pre-signed URL generation."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension (pdf, docx, txt, doc)")
    file_size: int = Field(
        ..., ge=1, le=50 * 1024 * 1024, description="File size in bytes (max 50MB)"
    )


class PresignedUrlResponse(BaseModel):
    """Response model containing pre-signed URL for S3 upload."""

    document_id: str = Field(..., description="UUID of the created document record")
    upload_url: str = Field(..., description="S3 endpoint URL for PUT request")
    s3_key: str = Field(..., description="S3 object key")
    content_type: str = Field(..., description="Content-Type header to use")
    expires_in: int = Field(default=300, description="URL expiration time in seconds")


class ProcessDocumentRequest(BaseModel):
    """Request model to trigger document processing."""

    document_id: str = Field(..., description="UUID of the document to process")


class ProcessDocumentResponse(BaseModel):
    """Response model for processing trigger."""

    document_id: str
    status: str
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


# ========== Background Processing ==========


def process_uploaded_document(
    document_id: uuid.UUID,
    s3_path: str,
    file_type: str,
    db_url: str,
) -> None:
    """
    Background task to process document from S3.

    This function:
    1. Downloads file from S3 to /tmp
    2. Creates new database session
    3. Calls DocumentProcessor.process_document_sync()
    4. Updates document status on success or failure
    5. Cleans up temp file

    Args:
        document_id: Document UUID
        s3_path: S3 URI (s3://bucket/key)
        file_type: File extension
        db_url: Database URL for creating new session
    """
    import os
    import tempfile

    import boto3
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    temp_file = None

    try:
        logger.info(f"Background processing started for document: {document_id}")

        # Parse S3 path (s3://bucket/key)
        if not s3_path.startswith("s3://"):
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        s3_path_parts = s3_path[5:].split("/", 1)
        if len(s3_path_parts) != 2:
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        bucket_name = s3_path_parts[0]
        s3_key = s3_path_parts[1]

        # Download file from S3 to temp location
        s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        # Use NamedTemporaryFile for secure temp file creation
        with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.info(f"Downloading {s3_path} to {temp_file_path}")
            s3_client.download_file(bucket_name, s3_key, temp_file_path)

            # Create new database session for background task
            engine = create_engine(db_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()

            try:
                # Process document
                processor = DocumentProcessor(db)
                result = processor.process_document_sync(document_id, temp_file_path, file_type)
                logger.info(f"Document processed successfully: {result}")
            finally:
                db.close()
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")

    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}", exc_info=True)

        # Update document status to failed
        try:
            engine = create_engine(db_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = "failed"
                    document.error_message = str(e)
                    db.commit()
            finally:
                db.close()
        except Exception as update_error:
            logger.error(f"Failed to update document status: {update_error}")

    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file {temp_file}: {cleanup_error}")


# ========== API Endpoints ==========


@router.post("/presigned-url", response_model=PresignedUrlResponse)
def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> PresignedUrlResponse:
    """
    Generate pre-signed S3 URL for direct client-to-S3 upload.

    This endpoint:
    1. Validates file type and size
    2. Creates Document record with status='pending'
    3. Generates pre-signed S3 POST URL
    4. Returns URL and required form fields

    Args:
        request: Pre-signed URL request
        current_user: Current authenticated user
        db: Database session

    Returns:
        PresignedUrlResponse: Pre-signed URL and upload details
    """
    try:
        # Validate file type
        file_type = request.file_type.lower().lstrip(".")
        if file_type not in settings.SUPPORTED_FILE_TYPES:
            supported_types = ", ".join(settings.SUPPORTED_FILE_TYPES)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_type}. Supported: {supported_types}",
            )

        # Create document record with status='pending'
        document_id = uuid.uuid4()
        document = Document(
            id=document_id,
            user_id=current_user.id,
            file_name=request.filename,
            file_path="",  # Will be set after S3 upload
            file_type=file_type,
            file_size=request.file_size,
            status="pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Created pending document record: {document_id}")

        # Generate pre-signed URL
        s3_service = get_s3_service()
        presigned_data = s3_service.generate_presigned_upload_url(
            document_id=str(document_id),
            filename=request.filename,
            file_type=file_type,
            expiration=300,  # 5 minutes
        )

        # Update document with S3 path
        document.file_path = presigned_data["s3_path"]
        db.commit()

        logger.info(f"Generated pre-signed URL for document: {document_id}")
        logger.info(f"Presigned URL: {presigned_data['url']}")

        return PresignedUrlResponse(
            document_id=str(document_id),
            upload_url=presigned_data["url"],
            s3_key=presigned_data["s3_key"],
            content_type=presigned_data["content_type"],
            expires_in=300,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate pre-signed URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}",
        )


@router.post("/process-document", response_model=ProcessDocumentResponse)
def trigger_document_processing(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> ProcessDocumentResponse:
    """
    Trigger document processing after S3 upload completes.

    This endpoint:
    1. Validates document exists and is 'pending'
    2. Triggers background processing via BackgroundTasks
    3. Returns processing status

    Args:
        request: Processing request with document_id
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session

    Returns:
        ProcessDocumentResponse: Processing status
    """
    try:
        # Validate UUID
        try:
            doc_uuid = uuid.UUID(request.document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format",
            )

        # Get document from database
        document = (
            db.query(Document)
            .filter(
                Document.id == doc_uuid,
                Document.user_id == current_user.id,
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized",
            )

        # Verify document is in pending state
        if document.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not in pending state (current: {document.status})",
            )

        # Verify file path is S3 path
        if not document.file_path.startswith("s3://"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not have a valid S3 path",
            )

        # Trigger background processing
        background_tasks.add_task(
            process_uploaded_document,
            document_id=doc_uuid,
            s3_path=document.file_path,
            file_type=document.file_type,
            db_url=settings.DATABASE_URL,
        )

        logger.info(f"Triggered processing for document: {doc_uuid}")

        return ProcessDocumentResponse(
            document_id=str(doc_uuid),
            status="processing",
            message="Document processing started in background",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger processing for {request.document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger document processing: {str(e)}",
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
