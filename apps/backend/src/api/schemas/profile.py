"""
Pydantic schemas for prompt profile API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    """Base profile model with all configurable fields."""

    name: str = Field(..., max_length=100, description="Profile name")
    description: str | None = Field(None, max_length=500, description="Profile description")
    system_prompt: str = Field(..., description="System prompt for non-RAG mode")
    rag_system_prompt_template: str = Field(
        ...,
        description="System prompt template for RAG mode (must contain {context} placeholder)",
    )
    chunk_size: int = Field(512, ge=100, le=2000, description="Document chunk size in characters")
    chunk_overlap: int = Field(128, ge=0, le=500, description="Chunk overlap size in characters")
    top_k_chunks: int = Field(10, ge=1, le=50, description="Number of chunks to retrieve")
    semantic_search_ratio: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Semantic search weight (0.0-1.0, remaining is BM25 weight)",
    )
    relevance_threshold: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score for retrieved chunks",
    )
    llm_model_id: str = Field(
        "amazon.nova-lite-v1:0",
        max_length=100,
        description="Bedrock LLM model identifier",
    )
    llm_temperature: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature for response generation",
    )
    llm_top_p: float = Field(
        0.9,
        ge=0.0,
        le=1.0,
        description="LLM top-p for response generation",
    )
    llm_max_tokens: int = Field(
        2048,
        ge=256,
        le=4096,
        description="Maximum tokens for LLM response",
    )


class ProfileCreateRequest(ProfileBase):
    """Request model for creating a new profile."""

    pass


class ProfileUpdateRequest(BaseModel):
    """Request model for updating an existing profile (all fields optional)."""

    name: str | None = Field(None, max_length=100, description="Profile name")
    description: str | None = Field(None, max_length=500, description="Profile description")
    system_prompt: str | None = Field(None, description="System prompt for non-RAG mode")
    rag_system_prompt_template: str | None = Field(
        None,
        description="System prompt template for RAG mode (must contain {context} placeholder)",
    )
    chunk_size: int | None = Field(None, ge=100, le=2000, description="Document chunk size")
    chunk_overlap: int | None = Field(None, ge=0, le=500, description="Chunk overlap size")
    top_k_chunks: int | None = Field(None, ge=1, le=50, description="Number of chunks to retrieve")
    semantic_search_ratio: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Semantic search weight",
    )
    relevance_threshold: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score",
    )
    llm_model_id: str | None = Field(
        None, max_length=100, description="Bedrock LLM model identifier"
    )
    llm_temperature: float | None = Field(None, ge=0.0, le=1.0, description="LLM temperature")
    llm_top_p: float | None = Field(None, ge=0.0, le=1.0, description="LLM top-p")
    llm_max_tokens: int | None = Field(None, ge=256, le=4096, description="Maximum tokens")


class ProfileResponse(BaseModel):
    """Response model for profile list (summary without prompts)."""

    id: str
    name: str
    description: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 ORM mode


class ProfileDetailResponse(ProfileResponse):
    """Response model for profile details (includes all fields)."""

    system_prompt: str
    rag_system_prompt_template: str
    chunk_size: int
    chunk_overlap: int
    top_k_chunks: int
    semantic_search_ratio: float
    relevance_threshold: float
    llm_model_id: str
    llm_temperature: float
    llm_top_p: float
    llm_max_tokens: int

    class Config:
        from_attributes = True  # Pydantic v2 ORM mode
