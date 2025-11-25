"""
Authentication service.

Simple authentication for demo purposes.
"""


def validate_user(username: str) -> bool:
    """
    Validate user credentials.

    For demo purposes, any non-empty username is valid.
    In production, implement proper authentication logic.

    Args:
        username: Username to validate

    Returns:
        bool: True if username is valid
    """
    return bool(username and username.strip())


def get_user_display_name(user_id: str) -> str:
    """
    Get display name for user.

    Args:
        user_id: User ID

    Returns:
        str: Display name
    """
    return user_id
