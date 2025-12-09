"""
Profile routes for managing prompt profiles.
"""

import uuid

from fastapi import APIRouter, status

from src.api.deps import CurrentUser, DBSession
from src.api.schemas.profile import (
    ProfileCreateRequest,
    ProfileDetailResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from src.services import profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileResponse])
def list_profiles(
    db: DBSession,
    current_user: CurrentUser,
) -> list[ProfileResponse]:
    """
    List all profiles for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        list[ProfileResponse]: List of user's profiles (sorted by is_default DESC, created_at ASC)
    """
    profiles = profile_service.get_user_profiles(db=db, user_id=current_user.id)

    return [
        ProfileResponse(
            id=str(profile.id),
            name=profile.name,
            description=profile.description,
            is_default=profile.is_default,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
        for profile in profiles
    ]


@router.get("/default", response_model=ProfileDetailResponse)
def get_default_profile(
    db: DBSession,
    current_user: CurrentUser,
) -> ProfileDetailResponse:
    """
    Get current default profile.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        ProfileDetailResponse: Default profile with all details
    """
    profile = profile_service.get_default_profile(db=db, user_id=current_user.id)

    return ProfileDetailResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        system_prompt=profile.system_prompt,
        rag_system_prompt_template=profile.rag_system_prompt_template,
        chunk_size=profile.chunk_size,
        chunk_overlap=profile.chunk_overlap,
        top_k_chunks=profile.top_k_chunks,
        semantic_search_ratio=profile.semantic_search_ratio,
        relevance_threshold=profile.relevance_threshold,
        llm_model_id=profile.llm_model_id,
        llm_temperature=profile.llm_temperature,
        llm_top_p=profile.llm_top_p,
        llm_max_tokens=profile.llm_max_tokens,
    )


@router.get("/{profile_id}", response_model=ProfileDetailResponse)
def get_profile(
    profile_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> ProfileDetailResponse:
    """
    Get profile details by ID.

    Args:
        profile_id: Profile ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        ProfileDetailResponse: Profile details

    Raises:
        HTTPException: If profile not found (HTTP 404)
    """
    profile = profile_service.get_profile_by_id(
        db=db,
        profile_id=uuid.UUID(profile_id),
        user_id=current_user.id,
    )

    if not profile:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return ProfileDetailResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        system_prompt=profile.system_prompt,
        rag_system_prompt_template=profile.rag_system_prompt_template,
        chunk_size=profile.chunk_size,
        chunk_overlap=profile.chunk_overlap,
        top_k_chunks=profile.top_k_chunks,
        semantic_search_ratio=profile.semantic_search_ratio,
        relevance_threshold=profile.relevance_threshold,
        llm_model_id=profile.llm_model_id,
        llm_temperature=profile.llm_temperature,
        llm_top_p=profile.llm_top_p,
        llm_max_tokens=profile.llm_max_tokens,
    )


@router.post("", response_model=ProfileDetailResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    request: ProfileCreateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ProfileDetailResponse:
    """
    Create a new profile.

    Args:
        request: Profile creation request
        db: Database session
        current_user: Current authenticated user

    Returns:
        ProfileDetailResponse: Created profile

    Raises:
        HTTPException: If validation fails (HTTP 400)
    """
    profile = profile_service.create_profile(
        db=db,
        user_id=current_user.id,
        name=request.name,
        system_prompt=request.system_prompt,
        rag_system_prompt_template=request.rag_system_prompt_template,
        description=request.description,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        top_k_chunks=request.top_k_chunks,
        semantic_search_ratio=request.semantic_search_ratio,
        relevance_threshold=request.relevance_threshold,
        llm_model_id=request.llm_model_id,
        llm_temperature=request.llm_temperature,
        llm_top_p=request.llm_top_p,
        llm_max_tokens=request.llm_max_tokens,
    )

    return ProfileDetailResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        system_prompt=profile.system_prompt,
        rag_system_prompt_template=profile.rag_system_prompt_template,
        chunk_size=profile.chunk_size,
        chunk_overlap=profile.chunk_overlap,
        top_k_chunks=profile.top_k_chunks,
        semantic_search_ratio=profile.semantic_search_ratio,
        relevance_threshold=profile.relevance_threshold,
        llm_model_id=profile.llm_model_id,
        llm_temperature=profile.llm_temperature,
        llm_top_p=profile.llm_top_p,
        llm_max_tokens=profile.llm_max_tokens,
    )


@router.put("/{profile_id}", response_model=ProfileDetailResponse)
def update_profile(
    profile_id: str,
    request: ProfileUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ProfileDetailResponse:
    """
    Update an existing profile.

    Args:
        profile_id: Profile ID
        request: Profile update request
        db: Database session
        current_user: Current authenticated user

    Returns:
        ProfileDetailResponse: Updated profile

    Raises:
        HTTPException: If profile not found or validation fails (HTTP 404/400)
    """
    profile = profile_service.update_profile(
        db=db,
        profile_id=uuid.UUID(profile_id),
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        rag_system_prompt_template=request.rag_system_prompt_template,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        top_k_chunks=request.top_k_chunks,
        semantic_search_ratio=request.semantic_search_ratio,
        relevance_threshold=request.relevance_threshold,
        llm_model_id=request.llm_model_id,
        llm_temperature=request.llm_temperature,
        llm_top_p=request.llm_top_p,
        llm_max_tokens=request.llm_max_tokens,
    )

    return ProfileDetailResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        system_prompt=profile.system_prompt,
        rag_system_prompt_template=profile.rag_system_prompt_template,
        chunk_size=profile.chunk_size,
        chunk_overlap=profile.chunk_overlap,
        top_k_chunks=profile.top_k_chunks,
        semantic_search_ratio=profile.semantic_search_ratio,
        relevance_threshold=profile.relevance_threshold,
        llm_model_id=profile.llm_model_id,
        llm_temperature=profile.llm_temperature,
        llm_top_p=profile.llm_top_p,
        llm_max_tokens=profile.llm_max_tokens,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """
    Delete a profile.

    Args:
        profile_id: Profile ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If profile not found or is default (HTTP 404/400)
    """
    profile_service.delete_profile(
        db=db,
        profile_id=uuid.UUID(profile_id),
        user_id=current_user.id,
    )


@router.post("/{profile_id}/set-default", status_code=status.HTTP_200_OK)
def set_default_profile(
    profile_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    """
    Set profile as default.

    Args:
        profile_id: Profile ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message

    Raises:
        HTTPException: If profile not found (HTTP 404)
    """
    profile_service.set_default_profile(
        db=db,
        profile_id=uuid.UUID(profile_id),
        user_id=current_user.id,
    )

    return {"message": "Profile set as default successfully"}
