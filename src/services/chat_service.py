"""
Chat service for handling conversations and messages.
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.bedrock_client import get_bedrock_client
from src.core.config import settings
from src.models import Conversation, Message, MessageRole
from src.prompts.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)


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


def generate_response(
    user_message: str,
    conversation_history: list[Message],
    db: Session | None = None,
    user_id: uuid.UUID | None = None,
) -> tuple[str, list[dict] | None]:
    """
    Generate response to user message using Claude Sonnet 4 via Bedrock.

    Args:
        user_message: User's message
        conversation_history: Previous messages in the conversation
        db: Database session (required if RAG is enabled)
        user_id: User ID (required if RAG is enabled)

    Returns:
        tuple: (Generated response, Retrieved chunks info or None)

    Raises:
        Exception: If the LLM call fails
    """
    try:
        # Limit conversation history to recent messages based on config
        max_history = settings.MAX_CONVERSATION_HISTORY * 2  # *2 for user+assistant pairs
        limited_history = conversation_history[-max_history:] if conversation_history else []

        logger.info(
            f"Generating response with {len(limited_history)} history messages "
            f"(limit: {settings.MAX_CONVERSATION_HISTORY} turns)"
        )

        # Initialize retrieved chunks
        retrieved_chunks = None
        retrieval_context = ""

        # Perform RAG retrieval if enabled
        if settings.ENABLE_RAG:
            if not db or not user_id:
                logger.warning("RAG enabled but db/user_id not provided, skipping retrieval")
            else:
                try:
                    from src.services.retrieval_service import get_retrieval_service

                    logger.info("Performing hybrid search for RAG context")

                    # Get retrieval service and perform hybrid search
                    retrieval_service = get_retrieval_service(db)
                    search_results = retrieval_service.hybrid_search(
                        query_text=user_message,
                        top_k=settings.TOP_K_CHUNKS,
                        user_id=user_id,
                    )

                    if search_results:
                        # Format retrieved chunks for context
                        context_parts = []
                        retrieved_chunks = []

                        for idx, result in enumerate(search_results, 1):
                            context_parts.append(
                                f"[Document {idx}: {result['file_name']}]\n"
                                f"{result['content']}\n"
                            )

                            retrieved_chunks.append(
                                {
                                    "chunk_id": result["chunk_id"],
                                    "document_id": result["document_id"],
                                    "file_name": result["file_name"],
                                    "score": result["score"],
                                    "semantic_score": result.get("semantic_score"),
                                    "bm25_score": result.get("bm25_score"),
                                }
                            )

                        retrieval_context = "\n".join(context_parts)
                        logger.info(
                            f"Retrieved {len(search_results)} chunks for RAG context "
                            f"(total {len(retrieval_context)} characters)"
                        )
                    else:
                        logger.info("No relevant documents found for user query")

                except Exception as e:
                    logger.error(f"RAG retrieval failed: {e}")
                    # Continue without RAG context rather than failing completely

        # Get system prompt with or without RAG context
        system_prompt = get_system_prompt(
            use_rag=settings.ENABLE_RAG, context=retrieval_context
        )

        # Get Bedrock client and invoke Claude
        bedrock_client = get_bedrock_client()
        response = bedrock_client.invoke_claude(
            user_message=user_message,
            conversation_history=limited_history,
            system_prompt=system_prompt,
        )

        logger.info("Response generated successfully")
        return response, retrieved_chunks

    except Exception as e:
        logger.error(f"Failed to generate response: {e}")

        # Check if this is a throttling error
        error_str = str(e)
        if "ThrottlingException" in error_str or "Too many requests" in error_str:
            error_msg = (
                "I'm currently experiencing high traffic and need to slow down. "
                "Please wait a few seconds and try again. "
                "If this persists, please wait 1-2 minutes before retrying."
            )
        else:
            # Return a generic user-friendly error message
            error_msg = (
                "Sorry, I encountered an issue processing your request. "
                "Please try again later or contact technical support."
            )

        return error_msg, None


def get_conversation_history(
    db: Session,
    conversation_id: uuid.UUID,
    limit: int | None = None,
) -> list[Message]:
    """
    Get conversation history.

    Args:
        db: Database session
        conversation_id: Conversation ID
        limit: Maximum number of messages to retrieve (defaults to config setting)

    Returns:
        list[Message]: List of messages
    """
    if limit is None:
        limit = settings.CONVERSATION_HISTORY_LIMIT

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
    limit: int | None = None,
) -> list[tuple[Conversation, int]]:
    """
    Get all conversations for a user with message counts.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of conversations to retrieve (defaults to config setting)

    Returns:
        list[tuple[Conversation, int]]: List of (conversation, message_count) tuples
    """
    if limit is None:
        limit = settings.USER_CONVERSATIONS_LIMIT

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
