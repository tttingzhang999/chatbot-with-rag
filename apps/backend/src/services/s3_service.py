"""
S3 service for handling file uploads with pre-signed URLs.

This module provides functionality to generate pre-signed URLs for direct
client-to-S3 uploads, eliminating the need for files to transit through
the backend Lambda function.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 operations including pre-signed URLs."""

    def __init__(self):
        """Initialize S3 client with configured region and bucket."""
        self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket_name = settings.DOCUMENT_BUCKET

    def generate_presigned_upload_url(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        expiration: int = 300,
    ) -> dict[str, any]:
        """
        Generate pre-signed URL for direct S3 upload from client.

        This method generates a pre-signed PUT URL that allows clients to
        upload files directly to S3 without routing through the backend.

        Args:
            document_id: UUID of the document record
            filename: Original filename
            file_type: File extension (pdf, docx, txt, doc)
            expiration: URL expiration time in seconds (default: 300 = 5 minutes)

        Returns:
            Dict containing:
                - url: S3 endpoint URL for PUT request
                - s3_key: Full S3 object key
                - s3_path: Full S3 URI (s3://bucket/key)
                - content_type: MIME type for the file

        Raises:
            ClientError: If S3 operation fails
        """
        # Construct S3 key with document ID and original filename
        unique_filename = f"{document_id}_{filename}"
        s3_key = f"uploads/{unique_filename}"
        content_type = self._get_content_type(file_type)

        try:
            # Generate pre-signed PUT URL (simpler than POST)
            presigned_url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                    "ContentType": content_type,
                    "Metadata": {
                        "document-id": document_id,
                        "file-type": file_type,
                    },
                },
                ExpiresIn=expiration,
            )

            logger.info(f"Generated pre-signed PUT URL for {s3_key} (expires in {expiration}s)")

            return {
                "url": presigned_url,
                "s3_key": s3_key,
                "s3_path": f"s3://{self.bucket_name}/{s3_key}",
                "content_type": content_type,
            }

        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL for {s3_key}: {e}")
            raise

    def delete_file(self, s3_uri: str) -> bool:
        """
        Delete file from S3 given s3://bucket/key URI.

        Args:
            s3_uri: S3 URI in format s3://bucket/key

        Returns:
            bool: True if deletion successful, False otherwise

        Raises:
            ValueError: If s3_uri format is invalid
        """
        try:
            if not s3_uri.startswith("s3://"):
                raise ValueError(f"Invalid S3 URI: {s3_uri}")

            # Parse s3://bucket/key
            parts = s3_uri[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""

            if not key:
                raise ValueError(f"No key found in S3 URI: {s3_uri}")

            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted S3 file: {s3_uri}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete S3 file {s3_uri}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting S3 file {s3_uri}: {str(e)}")
            return False

    def _get_content_type(self, file_type: str) -> str:
        """
        Get MIME type for file extension.

        Args:
            file_type: File extension (pdf, docx, txt, doc)

        Returns:
            MIME type string
        """
        content_types = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
        }
        return content_types.get(file_type.lower(), "application/octet-stream")


def get_s3_service() -> S3Service:
    """
    Get S3 service instance.

    Returns:
        S3Service: Configured S3 service instance
    """
    return S3Service()
