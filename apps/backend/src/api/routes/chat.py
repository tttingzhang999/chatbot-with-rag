"""
Chat routes for conversation management and messaging.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.api.deps import CurrentUser, DBSession
from src.models import MessageRole
from src.services import chat_service, profile_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    conversation_id: str | None = None
    profile_id: str | None = None  # Optional profile ID, uses default if not provided


class MessageResponse(BaseModel):
    """Message response model."""

    id: str
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    """Chat response model."""

    conversation_id: str
    messages: list[MessageResponse]


class ConversationListItem(BaseModel):
    """Conversation list item model."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    """Conversation list response model."""

    conversations: list[ConversationListItem]


class ConversationHistoryResponse(BaseModel):
    """Conversation history response model."""

    conversation_id: str
    messages: list[MessageResponse]


@router.post("/message", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ChatResponse:
    """
    Send a message and get response.

    Args:
        request: Chat request with message, optional conversation_id, and optional profile_id
        db: Database session
        current_user: Current user ID

    Returns:
        ChatResponse: Response with conversation ID and messages
    """
    # Get profile: use specified profile_id or default profile
    if request.profile_id:
        profile = profile_service.get_profile_by_id(
            db=db,
            profile_id=uuid.UUID(request.profile_id),
            user_id=current_user.id,
        )
        if not profile:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
    else:
        profile = profile_service.get_default_profile(db=db, user_id=current_user.id)

    # Get or create conversation
    conversation = chat_service.get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        profile_id=profile.id,
        conversation_id=request.conversation_id,
    )

    # Get conversation history
    history = chat_service.get_conversation_history(db=db, conversation_id=conversation.id)

    # Generate title for new conversations (first message)
    if not history:  # No previous messages means this is the first message
        title = chat_service.generate_conversation_title(request.message)
        conversation.title = title
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_message = chat_service.save_message(
        db=db,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request.message,
    )

    # Generate response with profile settings
    assistant_content, retrieved_chunks = chat_service.generate_response(
        user_message=request.message,
        conversation_history=history,
        profile=profile,
        db=db,
        user_id=current_user.id,
    )

    # Save assistant message with retrieved chunks
    assistant_message = chat_service.save_message(
        db=db,
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=assistant_content,
        retrieved_chunks=retrieved_chunks,
    )

    return ChatResponse(
        conversation_id=str(conversation.id),
        messages=[
            MessageResponse(
                id=str(user_message.id),
                role=user_message.role,
                content=user_message.content,
                created_at=user_message.created_at,
            ),
            MessageResponse(
                id=str(assistant_message.id),
                role=assistant_message.role,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
            ),
        ],
    )


@router.get("/conversations", response_model=ConversationListResponse)
def get_conversations(
    db: DBSession,
    current_user: CurrentUser,
    profile_id: str | None = Query(None, description="Filter by profile ID"),
) -> ConversationListResponse:
    """
    Get all conversations for current user, optionally filtered by profile.

    Args:
        db: Database session
        current_user: Current user ID
        profile_id: Optional profile ID to filter conversations

    Returns:
        ConversationListResponse: Response with list of conversations
    """
    # If profile_id not provided, use default profile
    if not profile_id:
        default_profile = profile_service.get_default_profile(db=db, user_id=current_user.id)
        profile_uuid = default_profile.id
    else:
        profile_uuid = uuid.UUID(profile_id)

    conversations = chat_service.get_user_conversations(
        db=db, user_id=current_user.id, profile_id=profile_uuid
    )

    conversation_items = [
        ConversationListItem(
            id=str(conv.id),
            title=conv.title or "Untitled Conversation",
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        )
        for conv, msg_count in conversations
    ]

    return ConversationListResponse(conversations=conversation_items)


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(
    conversation_id: str,
    db: DBSession,
    _current_user: CurrentUser,
) -> ConversationHistoryResponse:
    """
    Get conversation history.

    Args:
        conversation_id: Conversation ID
        db: Database session
        current_user: Current user ID

    Returns:
        ConversationHistoryResponse: Conversation history with messages
    """
    conv_uuid = uuid.UUID(conversation_id)
    messages = chat_service.get_conversation_history(db=db, conversation_id=conv_uuid)

    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=[
            MessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
    )


@router.post("/conversations", response_model=dict)
def create_conversation(
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    """
    Create a new conversation.

    Args:
        db: Database session
        current_user: Current user ID

    Returns:
        dict: New conversation info
    """
    conversation = chat_service.get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=None,
    )

    return {
        "conversation_id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation ID
        db: Database session
        current_user: Current user ID

    Returns:
        dict: Deletion status
    """
    conv_uuid = uuid.UUID(conversation_id)
    success = chat_service.delete_conversation(
        db=db,
        conversation_id=conv_uuid,
        user_id=current_user.id,
    )

    return {"success": success, "message": "Conversation deleted" if success else "Not found"}
