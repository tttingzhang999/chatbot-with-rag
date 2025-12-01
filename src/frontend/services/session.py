"""
User session and state management.
"""


class SessionManager:
    """Manages user session state and conversation context."""

    def __init__(self):
        self._current_user = {
            "user_id": None,
            "username": None,
            "email": None,
            "access_token": None,
        }
        self._current_conversation_id = None

    # User session methods
    def set_user(self, user_id: str, username: str, email: str, access_token: str):
        """Set current user session."""
        self._current_user["user_id"] = user_id
        self._current_user["username"] = username
        self._current_user["email"] = email
        self._current_user["access_token"] = access_token

    def clear_user(self):
        """Clear current user session."""
        self._current_user["user_id"] = None
        self._current_user["username"] = None
        self._current_user["email"] = None
        self._current_user["access_token"] = None

    def get_access_token(self) -> str | None:
        """Get current access token."""
        return self._current_user["access_token"]

    def get_username(self) -> str | None:
        """Get current username."""
        return self._current_user["username"]

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._current_user["access_token"] is not None

    def get_auth_headers(self) -> dict:
        """Get authorization headers with JWT token."""
        if self._current_user["access_token"]:
            return {"Authorization": f"Bearer {self._current_user['access_token']}"}
        return {}

    # Conversation methods
    def set_conversation_id(self, conversation_id: str | None):
        """Set current conversation ID."""
        self._current_conversation_id = conversation_id

    def get_conversation_id(self) -> str | None:
        """Get current conversation ID."""
        return self._current_conversation_id

    def clear_conversation(self):
        """Clear current conversation."""
        self._current_conversation_id = None

    def reset(self):
        """Reset all session state."""
        self.clear_user()
        self.clear_conversation()


# Global session instance
session = SessionManager()
