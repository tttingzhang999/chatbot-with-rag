"""
File upload routes.
"""

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from src.api.deps import CurrentUser

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Upload response model."""

    filename: str
    size: int
    content_type: str
    message: str


@router.post("/document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
) -> UploadResponse:
    """
    Upload a document.

    Currently accepts file but does not process it.
    In production, this would:
    1. Upload to S3
    2. Trigger Lambda for processing
    3. Generate embeddings and store in database

    Args:
        file: Uploaded file
        current_user: Current user ID

    Returns:
        UploadResponse: Upload confirmation
    """
    # Read file content (but don't process yet)
    content = await file.read()
    file_size = len(content)

    # In production, upload to S3 and trigger processing
    # For now, just return confirmation
    return UploadResponse(
        filename=file.filename or "unknown",
        size=file_size,
        content_type=file.content_type or "application/octet-stream",
        message=f"File received ({file_size} bytes). Processing not yet implemented.",
    )
