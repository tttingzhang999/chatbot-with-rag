"""
Unified HTTP API client for backend communication.
"""

import requests

from src.core.config import settings
from src.frontend.services.session import session


class APIClient:
    """HTTP client for communicating with FastAPI backend."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.BACKEND_API_URL

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        files: list | None = None,
        timeout: int | None = None,
        use_auth: bool = True,
    ) -> requests.Response:
        """
        Make HTTP request to backend API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path (e.g., '/auth/login')
            json: JSON request body
            files: Files for multipart upload
            timeout: Request timeout in seconds
            use_auth: Whether to include auth headers

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: On request error
        """
        url = f"{self.base_url}{endpoint}"
        headers = session.get_auth_headers() if use_auth else {}
        timeout = timeout or settings.HTTP_TIMEOUT_DEFAULT

        return requests.request(
            method=method,
            url=url,
            json=json,
            files=files,
            headers=headers,
            timeout=timeout,
        )

    # Auth endpoints
    def register(
        self, username: str, email: str, password: str, full_name: str | None = None
    ) -> requests.Response:
        """Register new user."""
        data = {
            "username": username,
            "email": email,
            "password": password,
        }
        if full_name:
            data["full_name"] = full_name

        return self._request(
            "POST",
            "/auth/register",
            json=data,
            timeout=settings.HTTP_TIMEOUT_SHORT,
            use_auth=False,
        )

    def login(self, username: str, password: str) -> requests.Response:
        """Login user."""
        return self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
            timeout=settings.HTTP_TIMEOUT_SHORT,
            use_auth=False,
        )

    # Chat endpoints
    def send_message(self, message: str, conversation_id: str | None = None) -> requests.Response:
        """Send chat message."""
        return self._request(
            "POST",
            "/chat/message",
            json={"message": message, "conversation_id": conversation_id},
            timeout=settings.HTTP_TIMEOUT_DEFAULT,
        )

    def get_conversations(self) -> requests.Response:
        """Get user's conversations."""
        return self._request("GET", "/chat/conversations", timeout=settings.HTTP_TIMEOUT_SHORT)

    def get_conversation(self, conversation_id: str) -> requests.Response:
        """Get specific conversation with messages."""
        return self._request(
            "GET",
            f"/chat/conversations/{conversation_id}",
            timeout=settings.HTTP_TIMEOUT_SHORT,
        )

    # Document endpoints
    def upload_documents(self, files: list) -> requests.Response:
        """Upload one or more documents."""
        return self._request(
            "POST",
            "/upload/document",
            files=files,
            timeout=settings.HTTP_TIMEOUT_UPLOAD,
        )

    def get_documents(self) -> requests.Response:
        """Get user's uploaded documents."""
        return self._request("GET", "/upload/documents", timeout=settings.HTTP_TIMEOUT_SHORT)

    def delete_document(self, document_id: str) -> requests.Response:
        """Delete a document."""
        return self._request(
            "DELETE",
            f"/upload/documents/{document_id}",
            timeout=settings.HTTP_TIMEOUT_SHORT,
        )


# Global API client instance
api = APIClient()
