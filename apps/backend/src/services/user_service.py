"""
User service for user management and authentication.
"""

import uuid

from sqlalchemy.orm import Session

from src.core.security import get_password_hash, verify_password
from src.models import User


def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Get user by username.

    Args:
        db: Database session
        username: Username to search for

    Returns:
        User | None: User if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get user by email.

    Args:
        db: Database session
        email: Email to search for

    Returns:
        User | None: User if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User | None: User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        username: Username
        email: Email address
        password: Plain text password (will be hashed)
        full_name: Optional full name

    Returns:
        User: Created user object
    """
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate user with username and password.

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        User | None: User if authentication successful, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def update_user(
    db: Session,
    user_id: uuid.UUID,
    **kwargs,
) -> User | None:
    """
    Update user information.

    Args:
        db: Database session
        user_id: User ID
        **kwargs: Fields to update

    Returns:
        User | None: Updated user if found, None otherwise
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key) and key != "id":
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
