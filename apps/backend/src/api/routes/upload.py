"""
File upload routes with pre-signed URL support and local storage fallback.

This module provides endpoints for:
1. Generating pre-signed S3 URLs for direct client-to-S3 uploads (if USE_PRESIGNED_URLS=True)
2. Direct file upload to local storage (if USE_PRESIGNED_URLS=False)
3. Triggering document processing after upload completes
4. Managing documents (list, delete)
"""

import logging
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from src.api.deps import CurrentUser, DBSession
from src.core.config import settings
from src.models.document import Document
from src.services import profile_service
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
    profile_id: str | None = Field(None, description="Profile ID (uses default if not provided)")


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
    storage_type: str
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


class ConfigResponse(BaseModel):
    """Configuration response model."""

    use_presigned_urls: bool = Field(..., description="Whether to use S3 presigned URLs")


class LocalUploadResponse(BaseModel):
    """Response model for local file upload."""

    document_id: str = Field(..., description="UUID of the created document record")
    status: str = Field(..., description="Upload and processing status")
    message: str = Field(..., description="Status message")


# ========== Helper Functions ==========


def ensure_upload_directory() -> Path:
    """
    Ensure upload directory exists.

    Returns:
        Path object for the upload directory

    Raises:
        RuntimeError: If directory cannot be created
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Upload directory ensured: {upload_dir}")
        return upload_dir
    except Exception as e:
        logger.error(f"Failed to create upload directory {upload_dir}: {e}")
        raise RuntimeError(f"Failed to create upload directory: {e}")


# ========== Background Processing ==========


def process_uploaded_document(
    document_id: uuid.UUID,
    file_path: str,
    file_type: str,
    db_url: str,
) -> None:
    """
    Background task to process document from S3 or local storage.

    This function:
    1. For S3 paths: Downloads file from S3 to /tmp
    2. For local paths: Uses file directly
    3. Creates new database session
    4. Calls DocumentProcessor.process_document_sync()
    5. Updates document status on success or failure
    6. Cleans up temp file (for S3 only, local files are kept)

    Args:
        document_id: Document UUID
        file_path: S3 URI (s3://bucket/key) or local file path
        file_type: File extension
        db_url: Database URL for creating new session
    """
    import tempfile

    import boto3
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    temp_file_path = None
    is_s3_file = file_path.startswith("s3://")

    try:
        logger.info(f"Background processing started for document: {document_id}")

        # Handle S3 files - download to temp location
        if is_s3_file:
            # Parse S3 path (s3://bucket/key)
            s3_path_parts = file_path[5:].split("/", 1)
            if len(s3_path_parts) != 2:
                raise ValueError(f"Invalid S3 path format: {file_path}")

            bucket_name = s3_path_parts[0]
            s3_key = s3_path_parts[1]

            # Download file from S3 to temp location
            s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
            # Use NamedTemporaryFile for secure temp file creation
            with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as temp_file:
                temp_file_path = temp_file.name

            logger.info(f"Downloading {file_path} to {temp_file_path}")
            s3_client.download_file(bucket_name, s3_key, temp_file_path)
            processing_file_path = temp_file_path
        else:
            # Local file - use directly
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Local file not found: {file_path}")
            processing_file_path = file_path
            logger.info(f"Processing local file: {file_path}")

        # Create new database session for background task
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Process document
            processor = DocumentProcessor(db)
            result = processor.process_document_sync(document_id, processing_file_path, file_type)
            logger.info(f"Document processed successfully: {result}")
        finally:
            db.close()

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
        # Clean up temp file (only for S3 downloads)
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {cleanup_error}")


# ========== API Endpoints ==========


@router.get("/config", response_model=ConfigResponse)
def get_upload_config() -> ConfigResponse:
    """
    Get upload configuration to determine upload mode.

    Returns:
        ConfigResponse: Upload configuration including USE_PRESIGNED_URLS setting
    """
    return ConfigResponse(use_presigned_urls=settings.USE_PRESIGNED_URLS)


@router.post("/local", response_model=LocalUploadResponse)
async def upload_local_file(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: DBSession,
    file: UploadFile = File(...),
    profile_id: str | None = Form(None),
) -> LocalUploadResponse:
    """
    Upload file to local storage and trigger processing.

    This endpoint is used when USE_PRESIGNED_URLS=False.
    It saves the file to local storage and immediately triggers processing.

    Args:
        file: Uploaded file
        profile_id: Optional profile ID (uses default if not provided)
        current_user: Current authenticated user
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        LocalUploadResponse: Upload status and document ID
    """
    try:
        # Get profile: use specified profile_id or default profile
        if profile_id:
            profile = profile_service.get_profile_by_id(
                db=db,
                profile_id=uuid.UUID(profile_id),
                user_id=current_user.id,
            )
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )
        else:
            profile = profile_service.get_default_profile(db=db, user_id=current_user.id)

        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.SUPPORTED_FILE_TYPES:
            supported_types = ", ".join(settings.SUPPORTED_FILE_TYPES)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported: {supported_types}",
            )

        # Ensure upload directory exists
        upload_dir = ensure_upload_directory()

        # Create document record
        document_id = uuid.uuid4()
        unique_filename = f"{document_id}_{file.filename}"
        file_path = upload_dir / unique_filename

        # Save file to disk
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"Saved file to local storage: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )

        # Get file size
        file_size = file_path.stat().st_size

        # Create document record in database
        document = Document(
            id=document_id,
            user_id=current_user.id,
            profile_id=profile.id,
            file_name=file.filename,
            file_path=str(file_path.absolute()),
            file_type=file_extension,
            file_size=file_size,
            storage_type="local",
            status="pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Created document record: {document_id}")

        # Trigger background processing immediately
        background_tasks.add_task(
            process_uploaded_document,
            document_id=document_id,
            file_path=str(file_path.absolute()),
            file_type=file_extension,
            db_url=settings.DATABASE_URL,
        )

        logger.info(f"Triggered processing for local file: {document_id}")

        return LocalUploadResponse(
            document_id=str(document_id),
            status="processing",
            message="File uploaded successfully and processing started",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload local file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.post("/presigned-url", response_model=PresignedUrlResponse)
def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: CurrentUser,
    db: DBSession,
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
        # Get profile: use specified profile_id or default profile
        if request.profile_id:
            profile = profile_service.get_profile_by_id(
                db=db,
                profile_id=uuid.UUID(request.profile_id),
                user_id=current_user.id,
            )
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )
        else:
            profile = profile_service.get_default_profile(db=db, user_id=current_user.id)

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
            profile_id=profile.id,
            file_name=request.filename,
            file_path="",  # Will be set after S3 upload
            file_type=file_type,
            file_size=request.file_size,
            storage_type="cloud",
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
    current_user: CurrentUser,
    db: DBSession,
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

        # Verify file path exists (S3 or local)
        if not document.file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document does not have a valid file path",
            )

        # Trigger background processing
        background_tasks.add_task(
            process_uploaded_document,
            document_id=doc_uuid,
            file_path=document.file_path,
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
    current_user: CurrentUser,
    db: DBSession,
    profile_id: str | None = Query(None, description="Filter by profile ID"),
) -> DocumentListResponse:
    """
    Get all documents uploaded by current user, optionally filtered by profile.

    Args:
        current_user: Current authenticated user
        db: Database session
        profile_id: Optional profile ID to filter documents

    Returns:
        DocumentListResponse: List of documents
    """
    try:
        # If profile_id not provided, use default profile
        if not profile_id:
            default_profile = profile_service.get_default_profile(db=db, user_id=current_user.id)
            profile_uuid = default_profile.id
        else:
            profile_uuid = uuid.UUID(profile_id)

        documents = get_user_documents(db, current_user.id, profile_uuid)

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
    current_user: CurrentUser,
    db: DBSession,
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
