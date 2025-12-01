"""
Application configuration using Pydantic settings.

All configuration values can be set via environment variables in .env file.
Secrets can optionally be loaded from AWS Secrets Manager.
"""

import logging
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings can be overridden via environment variables.
    See .env.example for documentation of each setting.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========== Application ==========
    APP_NAME: str = Field(
        default="HR Chatbot",
        description="Application name displayed in UI and logs",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode for development",
    )

    # ========== Security ==========
    SECRET_KEY: str = Field(
        default="",
        description="Secret key for JWT token signing. Can be loaded from Secrets Manager via APP_SECRET_NAME",
    )
    APP_SECRET_NAME: str = Field(
        default="",
        description="Optional: AWS Secrets Manager secret name for app secrets (secret_key, algorithm)",
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,
        description="JWT token expiration time in minutes (default: 7 days)",
    )

    # ========== Server Configuration ==========
    UVICORN_HOST: str = Field(
        default="0.0.0.0",
        description="FastAPI/Uvicorn server host",
    )
    UVICORN_PORT: int = Field(
        default=8000,
        description="FastAPI/Uvicorn server port",
        ge=1024,
        le=65535,
    )
    UVICORN_RELOAD: bool = Field(
        default=False,
        description="Enable auto-reload for development (set to True in dev mode)",
    )
    GRADIO_HOST: str = Field(
        default="0.0.0.0",
        description="Gradio frontend server host",
    )
    GRADIO_PORT: int = Field(
        default=7860,
        description="Gradio frontend server port",
        ge=1024,
        le=65535,
    )

    # ========== API Configuration ==========
    API_TITLE: str = Field(
        default="HR Chatbot API",
        description="API title shown in OpenAPI docs",
    )
    API_DESCRIPTION: str = Field(
        default="API for HR Chatbot with RAG capabilities",
        description="API description shown in OpenAPI docs",
    )
    API_VERSION: str = Field(
        default="0.3.0",
        description="API version number",
    )
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (use specific origins in production)",
    )

    # ========== AWS Configuration ==========
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock and other services",
    )
    AWS_PROFILE: str | None = Field(
        default=None,
        description="AWS profile name (optional, for local development)",
    )

    # ========== Database ==========
    DB_SECRET_NAME: str = Field(
        default="",
        description="Optional: AWS Secrets Manager secret name for database credentials. If set, overrides DATABASE_URL",
    )
    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL connection string. Can be loaded from Secrets Manager via DB_SECRET_NAME",
    )
    CONVERSATION_HISTORY_LIMIT: int = Field(
        default=50,
        description="Maximum number of messages to retrieve for conversation history",
        ge=1,
    )
    USER_CONVERSATIONS_LIMIT: int = Field(
        default=20,
        description="Maximum number of conversations to retrieve for a user",
        ge=1,
    )

    # ========== S3 Configuration ==========
    DOCUMENT_BUCKET: str = Field(
        default="",
        description="Optional: S3 bucket name for document storage (only needed when using S3)",
    )

    # ========== File Upload Configuration ==========
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Local directory for temporary file uploads",
    )
    SUPPORTED_FILE_TYPES: list[str] = Field(
        default=["pdf", "txt", "docx", "doc"],
        description="List of supported file extensions (without leading dot)",
    )

    # ========== Frontend Configuration ==========
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API URL for frontend to connect to",
    )
    ASSETS_DIR: str = Field(
        default="assets",
        description="Directory containing frontend assets (avatars, images, etc.)",
    )
    BOT_AVATAR_FILENAME: str = Field(
        default="bot_avatar.png",
        description="Filename of bot avatar image in assets directory",
    )

    # ========== HTTP Configuration ==========
    HTTP_TIMEOUT_DEFAULT: int = Field(
        default=30,
        description="Default HTTP request timeout in seconds",
        ge=1,
    )
    HTTP_TIMEOUT_UPLOAD: int = Field(
        default=30,
        description="HTTP timeout for file upload requests in seconds",
        ge=1,
    )
    HTTP_TIMEOUT_SHORT: int = Field(
        default=30,
        description="HTTP timeout for quick requests (status checks, etc.) in seconds",
        ge=1,
    )

    # ========== Bedrock Models ==========
    LLM_MODEL_ID: str = Field(
        default="anthropic.claude-3-5-sonnet-20240620-v1:0",
        description="Amazon Bedrock LLM model ID",
    )
    EMBEDDING_MODEL_ID: str = Field(
        default="cohere.embed-v4:0",
        description="Amazon Bedrock embedding model ID",
    )

    # ========== LLM Configuration ==========
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="LLM sampling temperature (0.0-1.0, higher = more creative)",
        ge=0.0,
        le=1.0,
    )
    LLM_TOP_P: float = Field(
        default=0.9,
        description="LLM nucleus sampling top-p value (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    LLM_MAX_TOKENS: int = Field(
        default=2048,
        description="Maximum tokens in LLM response",
        ge=1,
    )
    MAX_CONVERSATION_HISTORY: int = Field(
        default=10,
        description="Number of recent conversation turns to include in context",
        ge=1,
    )

    # ========== RAG Configuration ==========
    CHUNK_SIZE: int = Field(
        default=512,
        description="Document chunk size in characters",
        ge=100,
    )
    CHUNK_OVERLAP: int = Field(
        default=128,
        description="Overlap between consecutive chunks in characters",
        ge=0,
    )
    TOP_K_CHUNKS: int = Field(
        default=10,
        description="Number of top chunks to retrieve for RAG",
        ge=1,
    )
    SEMANTIC_SEARCH_RATIO: float = Field(
        default=0.5,
        description="Ratio of semantic search in hybrid search (0.5 = 50% semantic, 50% BM25)",
        ge=0.0,
        le=1.0,
    )
    RELEVANCE_THRESHOLD: float = Field(
        default=0.3,
        description="Minimum relevance score threshold for RAG retrieval (0.0-1.0, higher = stricter)",
        ge=0.0,
        le=1.0,
    )
    ENABLE_RAG: bool = Field(
        default=False,
        description="Toggle RAG functionality on/off",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=1536,
        description="Embedding vector dimension (Cohere Embed v4 via Bedrock uses 1536)",
        ge=1,
    )

    @field_validator("UVICORN_PORT", "GRADIO_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is in valid range."""
        if not (1024 <= v <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {v}")
        return v

    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Validate chunk overlap is less than chunk size."""
        # Note: chunk_size might not be set yet during validation
        # We'll do runtime validation in the document service
        if v < 0:
            raise ValueError("Chunk overlap must be non-negative")
        return v

    @field_validator("SUPPORTED_FILE_TYPES")
    @classmethod
    def validate_file_types(cls, v: list[str]) -> list[str]:
        """Ensure file types are lowercase and without leading dots."""
        return [ext.lower().lstrip(".") for ext in v]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Support comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v


def _load_settings() -> Settings:
    """
    Load settings with optional Secrets Manager integration.

    If DB_SECRET_NAME or APP_SECRET_NAME are set, they will be loaded from
    AWS Secrets Manager and override the corresponding environment variables.

    Returns:
        Settings instance with all configuration loaded
    """
    # First, create settings from environment variables
    base_settings = Settings()

    # Check if we need to load from Secrets Manager
    use_secrets_manager = bool(base_settings.DB_SECRET_NAME or base_settings.APP_SECRET_NAME)

    if not use_secrets_manager:
        logger.info("Using configuration from environment variables only")
        return base_settings

    logger.info("Loading secrets from AWS Secrets Manager...")

    try:
        from src.core.secrets import get_secrets_manager

        sm = get_secrets_manager(region_name=base_settings.AWS_REGION)

        # Load database credentials if DB_SECRET_NAME is set
        if base_settings.DB_SECRET_NAME:
            logger.info(f"Loading database URL from secret: {base_settings.DB_SECRET_NAME}")
            database_url = sm.build_database_url(base_settings.DB_SECRET_NAME)
            # Override DATABASE_URL in environment
            os.environ["DATABASE_URL"] = database_url

        # Load app secrets if APP_SECRET_NAME is set
        if base_settings.APP_SECRET_NAME:
            logger.info(f"Loading app secrets from: {base_settings.APP_SECRET_NAME}")
            app_secrets = sm.get_app_secrets(base_settings.APP_SECRET_NAME)

            # Override SECRET_KEY in environment
            if "secret_key" in app_secrets:
                os.environ["SECRET_KEY"] = app_secrets["secret_key"]

            # Optionally override ALGORITHM if provided
            if "algorithm" in app_secrets:
                os.environ["ALGORITHM"] = app_secrets["algorithm"]

        # Recreate settings with updated environment variables
        logger.info("Secrets loaded successfully from AWS Secrets Manager")
        return Settings()

    except ImportError as e:
        logger.error(f"Failed to import secrets module: {e}")
        logger.warning("Falling back to environment variables only")
        return base_settings
    except Exception as e:
        logger.error(f"Failed to load secrets from Secrets Manager: {e}")
        logger.warning("Falling back to environment variables only")
        return base_settings


settings = _load_settings()
