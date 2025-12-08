"""
Authentication routes for user registration and login.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.api.deps import DBSession
from src.core.security import create_access_token
from src.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Registration request model."""

    username: str
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str
    user_id: str
    username: str
    email: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: DBSession) -> TokenResponse:
    """
    Register a new user.

    Args:
        request: Registration request with username, email, and password
        db: Database session

    Returns:
        TokenResponse: JWT access token and user info

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    if user_service.get_user_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    if user_service.get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = user_service.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",  # nosec B106 - "bearer" is OAuth2 standard token type
        user_id=str(user.id),
        username=user.username,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: DBSession) -> TokenResponse:
    """
    Login with username and password.

    Args:
        request: Login request with username and password
        db: Database session

    Returns:
        TokenResponse: JWT access token and user info

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = user_service.authenticate_user(db, request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",  # nosec B106 - "bearer" is OAuth2 standard token type
        user_id=str(user.id),
        username=user.username,
        email=user.email,
    )
