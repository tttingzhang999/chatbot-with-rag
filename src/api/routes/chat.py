"""
Chat routes for conversation management and messaging.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.deps import CurrentUser, DBSession
from src.models import MessageRole
from src.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    conversation_id: str | None = None


class MessageResponse(BaseModel):
    """Message response model."""

    id: str
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    """Chat response model."""

    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationListItem(BaseModel):
    """Conversation list item model."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


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
        request: Chat request with message and optional conversation_id
        db: Database session
        current_user: Current user ID

    Returns:
        ChatResponse: Response with conversation ID and messages
    """
    # Get or create conversation
    conversation = chat_service.get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
    )

    # Get conversation history
    history = chat_service.get_conversation_history(db=db, conversation_id=conversation.id)

    # Save user message
    user_message = chat_service.save_message(
        db=db,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request.message,
    )

    # Generate response with RAG
    assistant_content, retrieved_chunks = chat_service.generate_response(
        user_message=request.message,
        conversation_history=history,
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
        user_message=MessageResponse(
            id=str(user_message.id),
            role=user_message.role,
            content=user_message.content,
            created_at=user_message.created_at,
        ),
        assistant_message=MessageResponse(
            id=str(assistant_message.id),
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
        ),
    )


@router.get("/conversations", response_model=list[ConversationListItem])
def get_conversations(
    db: DBSession,
    current_user: CurrentUser,
) -> list[ConversationListItem]:
    """
    Get all conversations for current user.

    Args:
        db: Database session
        current_user: Current user ID

    Returns:
        list[ConversationListItem]: List of conversations
    """
    conversations = chat_service.get_user_conversations(db=db, user_id=current_user.id)

    return [
        ConversationListItem(
            id=str(conv.id),
            title=conv.title or "Untitled Conversation",
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        )
        for conv, msg_count in conversations
    ]


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
