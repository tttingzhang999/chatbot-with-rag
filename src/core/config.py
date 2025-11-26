"""
Application configuration using Pydantic settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "HR Chatbot"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str  # Required: Secret key for JWT token signing
    ALGORITHM: str = "HS256"  # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_PROFILE: str | None = None

    # Database
    DB_SECRET_NAME: str = ""  # Optional: Only needed for AWS Secrets Manager
    DATABASE_URL: str  # Required: PostgreSQL connection string

    # S3
    DOCUMENT_BUCKET: str = ""  # Optional: Only needed when using S3

    # Bedrock Models
    LLM_MODEL_ID: str = "anthropic.claude-sonnet-4"
    EMBEDDING_MODEL_ID: str = "cohere.embed-v4"

    # LLM Configuration
    LLM_TEMPERATURE: float = 0.7
    LLM_TOP_P: float = 0.9
    LLM_MAX_TOKENS: int = 2048
    MAX_CONVERSATION_HISTORY: int = 10  # Number of recent conversation turns to include

    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_CHUNKS: int = 10
    SEMANTIC_SEARCH_RATIO: float = 0.5  # 50% semantic, 50% BM25
    ENABLE_RAG: bool = False  # Toggle RAG functionality

    # Cohere Embed v4 dimensions
    EMBEDDING_DIMENSION: int = 1024


settings = Settings()
