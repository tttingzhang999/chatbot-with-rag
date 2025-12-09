"""
Profile service for managing prompt profiles.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.models.prompt_profile import PromptProfile
from src.prompts.system_prompts import (
    HR_ADVISOR_RAG_SYSTEM_PROMPT_TEMPLATE,
    HR_ADVISOR_SYSTEM_PROMPT,
)


def get_user_profiles(db: Session, user_id: uuid.UUID) -> list[PromptProfile]:
    """
    Get all profiles for a user, sorted by is_default DESC, created_at ASC.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List[PromptProfile]: List of user's profiles
    """
    return (
        db.query(PromptProfile)
        .filter(PromptProfile.user_id == user_id)
        .order_by(PromptProfile.is_default.desc(), PromptProfile.created_at.asc())
        .all()
    )


def get_profile_by_id(
    db: Session, profile_id: uuid.UUID, user_id: uuid.UUID
) -> PromptProfile | None:
    """
    Get profile by ID, verify ownership.

    Args:
        db: Database session
        profile_id: Profile ID
        user_id: User ID (for ownership verification)

    Returns:
        PromptProfile | None: Profile if found and owned by user, None otherwise
    """
    return (
        db.query(PromptProfile)
        .filter(
            and_(
                PromptProfile.id == profile_id,
                PromptProfile.user_id == user_id,
            )
        )
        .first()
    )


def get_default_profile(db: Session, user_id: uuid.UUID) -> PromptProfile:
    """
    Get default profile for user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        PromptProfile: Default profile

    Raises:
        HTTPException: If no default profile found (HTTP 404)
    """
    profile = (
        db.query(PromptProfile)
        .filter(
            and_(
                PromptProfile.user_id == user_id,
                PromptProfile.is_default == True,  # noqa: E712
            )
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default profile found for user",
        )

    return profile


def create_profile(
    db: Session,
    user_id: uuid.UUID,
    name: str,
    system_prompt: str,
    rag_system_prompt_template: str,
    description: str | None = None,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    top_k_chunks: int = 10,
    semantic_search_ratio: float = 0.5,
    relevance_threshold: float = 0.3,
    llm_model_id: str = "amazon.nova-lite-v1:0",
    llm_temperature: float = 0.7,
    llm_top_p: float = 0.9,
    llm_max_tokens: int = 2048,
) -> PromptProfile:
    """
    Create a new profile with validation.

    Args:
        db: Database session
        user_id: User ID
        name: Profile name
        system_prompt: System prompt (non-RAG)
        rag_system_prompt_template: RAG system prompt template (must contain {context})
        description: Optional profile description
        chunk_size: Document chunk size (100-2000)
        chunk_overlap: Chunk overlap size (0-500)
        top_k_chunks: Number of chunks to retrieve (1-50)
        semantic_search_ratio: Semantic vs BM25 ratio (0.0-1.0)
        relevance_threshold: Minimum relevance score (0.0-1.0)
        llm_model_id: LLM model identifier
        llm_temperature: LLM temperature (0.0-1.0)
        llm_top_p: LLM top_p (0.0-1.0)
        llm_max_tokens: LLM max tokens (256-4096)

    Returns:
        PromptProfile: Created profile

    Raises:
        HTTPException: If validation fails (HTTP 400)
    """
    # Validate unique name per user
    existing = (
        db.query(PromptProfile)
        .filter(
            and_(
                PromptProfile.user_id == user_id,
                PromptProfile.name == name,
            )
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile with name '{name}' already exists",
        )

    # Validate RAG template contains {context} placeholder
    if "{context}" not in rag_system_prompt_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rag_system_prompt_template must contain {context} placeholder",
        )

    # Validate numeric ranges (additional validation beyond DB constraints)
    if not (100 <= chunk_size <= 2000):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_size must be between 100 and 2000",
        )

    if not (0 <= chunk_overlap <= 500):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be between 0 and 500",
        )

    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be less than chunk_size",
        )

    # Check if this is user's first profile, make it default
    user_profiles_count = db.query(PromptProfile).filter(PromptProfile.user_id == user_id).count()

    is_default = user_profiles_count == 0

    profile = PromptProfile(
        user_id=user_id,
        name=name,
        description=description,
        is_default=is_default,
        system_prompt=system_prompt,
        rag_system_prompt_template=rag_system_prompt_template,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k_chunks=top_k_chunks,
        semantic_search_ratio=semantic_search_ratio,
        relevance_threshold=relevance_threshold,
        llm_model_id=llm_model_id,
        llm_temperature=llm_temperature,
        llm_top_p=llm_top_p,
        llm_max_tokens=llm_max_tokens,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def update_profile(
    db: Session,
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
    system_prompt: str | None = None,
    rag_system_prompt_template: str | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    top_k_chunks: int | None = None,
    semantic_search_ratio: float | None = None,
    relevance_threshold: float | None = None,
    llm_model_id: str | None = None,
    llm_temperature: float | None = None,
    llm_top_p: float | None = None,
    llm_max_tokens: int | None = None,
) -> PromptProfile:
    """
    Update profile with validation.

    Args:
        db: Database session
        profile_id: Profile ID
        user_id: User ID (for ownership verification)
        ... (all other fields are optional)

    Returns:
        PromptProfile: Updated profile

    Raises:
        HTTPException: If profile not found or validation fails
    """
    profile = get_profile_by_id(db, profile_id, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Validate unique name if changing
    if name is not None and name != profile.name:
        existing = (
            db.query(PromptProfile)
            .filter(
                and_(
                    PromptProfile.user_id == user_id,
                    PromptProfile.name == name,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile with name '{name}' already exists",
            )

        profile.name = name

    # Validate RAG template if changing
    if rag_system_prompt_template is not None:
        if "{context}" not in rag_system_prompt_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rag_system_prompt_template must contain {context} placeholder",
            )
        profile.rag_system_prompt_template = rag_system_prompt_template

    # Update other fields if provided
    if description is not None:
        profile.description = description

    if system_prompt is not None:
        profile.system_prompt = system_prompt

    if chunk_size is not None:
        if not (100 <= chunk_size <= 2000):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_size must be between 100 and 2000",
            )
        profile.chunk_size = chunk_size

    if chunk_overlap is not None:
        if not (0 <= chunk_overlap <= 500):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_overlap must be between 0 and 500",
            )
        profile.chunk_overlap = chunk_overlap

    # Validate chunk_overlap < chunk_size after both might have changed
    if profile.chunk_overlap >= profile.chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be less than chunk_size",
        )

    if top_k_chunks is not None:
        profile.top_k_chunks = top_k_chunks

    if semantic_search_ratio is not None:
        profile.semantic_search_ratio = semantic_search_ratio

    if relevance_threshold is not None:
        profile.relevance_threshold = relevance_threshold

    if llm_model_id is not None:
        profile.llm_model_id = llm_model_id

    if llm_temperature is not None:
        profile.llm_temperature = llm_temperature

    if llm_top_p is not None:
        profile.llm_top_p = llm_top_p

    if llm_max_tokens is not None:
        profile.llm_max_tokens = llm_max_tokens

    db.commit()
    db.refresh(profile)

    return profile


def delete_profile(db: Session, profile_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """
    Delete profile (except default).

    Args:
        db: Database session
        profile_id: Profile ID
        user_id: User ID (for ownership verification)

    Raises:
        HTTPException: If profile not found or is default (HTTP 404/400)
    """
    profile = get_profile_by_id(db, profile_id, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    if profile.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default profile",
        )

    db.delete(profile)
    db.commit()


def set_default_profile(db: Session, profile_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """
    Set profile as default, unset previous default.

    Args:
        db: Database session
        profile_id: Profile ID
        user_id: User ID (for ownership verification)

    Raises:
        HTTPException: If profile not found (HTTP 404)
    """
    profile = get_profile_by_id(db, profile_id, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    # Unset all user's profiles as default
    db.query(PromptProfile).filter(PromptProfile.user_id == user_id).update({"is_default": False})

    # Set target profile as default
    profile.is_default = True

    db.commit()


def create_default_profile(db: Session, user_id: uuid.UUID) -> PromptProfile:
    """
    Create default profile for new user with HR prompts as initial values.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        PromptProfile: Created default profile
    """
    profile = PromptProfile(
        user_id=user_id,
        name="Default Profile",
        description="Default RAG chatbot profile with HR-focused prompts",
        is_default=True,
        system_prompt=HR_ADVISOR_SYSTEM_PROMPT,
        rag_system_prompt_template=HR_ADVISOR_RAG_SYSTEM_PROMPT_TEMPLATE,
        chunk_size=512,
        chunk_overlap=128,
        top_k_chunks=10,
        semantic_search_ratio=0.5,
        relevance_threshold=0.3,
        llm_model_id="amazon.nova-lite-v1:0",
        llm_temperature=0.7,
        llm_top_p=0.9,
        llm_max_tokens=2048,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile
