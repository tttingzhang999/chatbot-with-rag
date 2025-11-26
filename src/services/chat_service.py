"""
Chat service for handling conversations and messages.
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Conversation, Message, MessageRole


def get_or_create_conversation(
    db: Session,
    user_id: uuid.UUID,
    conversation_id: str | None = None,
) -> Conversation:
    """
    Get existing conversation or create a new one.

    Args:
        db: Database session
        user_id: User ID
        conversation_id: Optional conversation ID to retrieve

    Returns:
        Conversation: Conversation object
    """
    if conversation_id:
        # Try to get existing conversation
        conv = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )
        if conv:
            return conv

    # Create new conversation
    conv = Conversation(
        user_id=user_id,
        title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def save_message(
    db: Session,
    conversation_id: uuid.UUID,
    role: MessageRole,
    content: str,
    retrieved_chunks: list | None = None,
) -> Message:
    """
    Save a message to the database.

    Args:
        db: Database session
        conversation_id: Conversation ID
        role: Message role (user/assistant)
        content: Message content
        retrieved_chunks: Optional list of retrieved chunk IDs

    Returns:
        Message: Created message object
    """
    message = Message(
        conversation_id=conversation_id,
        role=role.value,
        content=content,
        retrieved_chunks=retrieved_chunks or [],
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def generate_response(user_message: str, conversation_history: list[Message]) -> str:
    """
    Generate response to user message.

    Currently implements simple echo for testing.
    In production, replace with LLM call (Claude Sonnet 4 via Bedrock).

    Args:
        user_message: User's message
        conversation_history: Previous messages in the conversation

    Returns:
        str: Generated response
    """
    # Simple echo response for testing
    response = f"Echo: {user_message}"

    # Add conversation context info
    if len(conversation_history) > 2:
        response += f"\n\n(這是我們的第 {len(conversation_history) // 2 + 1} 輪對話)"

    return response


def get_conversation_history(
    db: Session,
    conversation_id: uuid.UUID,
    limit: int = 50,
) -> list[Message]:
    """
    Get conversation history.

    Args:
        db: Database session
        conversation_id: Conversation ID
        limit: Maximum number of messages to retrieve

    Returns:
        list[Message]: List of messages
    """
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
        .all()
    )


def get_user_conversations(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[tuple[Conversation, int]]:
    """
    Get all conversations for a user with message counts.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of conversations to retrieve

    Returns:
        list[tuple[Conversation, int]]: List of (conversation, message_count) tuples
    """
    # Use a subquery to count messages for each conversation efficiently
    message_count_subquery = (
        db.query(
            Message.conversation_id,
            func.count(Message.id).label("message_count"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    # Join conversations with message counts
    results = (
        db.query(Conversation, func.coalesce(message_count_subquery.c.message_count, 0))
        .outerjoin(
            message_count_subquery,
            Conversation.id == message_count_subquery.c.conversation_id,
        )
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .all()
    )

    return results


def delete_conversation(db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Delete a conversation.

    Args:
        db: Database session
        conversation_id: Conversation ID
        user_id: User ID (for authorization)

    Returns:
        bool: True if deleted successfully
    """
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conv:
        return False

    db.delete(conv)
    db.commit()
    return True
