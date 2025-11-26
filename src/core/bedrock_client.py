"""
Amazon Bedrock client for LLM and embedding operations.

This module provides a wrapper around AWS Bedrock services for:
- Claude Sonnet 4 LLM invocations
- Conversation history management
- Error handling and retries
"""

import logging
from typing import Any

import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.core.config import settings
from src.models.conversation import Message

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for interacting with Amazon Bedrock services."""

    def __init__(self):
        """Initialize Bedrock client with AWS configuration."""
        # Initialize boto3 session
        # When using AWS Vault, credentials are set via environment variables,
        # so we only specify the region and let boto3 use the default credential chain
        self.session = boto3.Session(region_name=settings.AWS_REGION)

        # Initialize ChatBedrock for Claude Sonnet 4
        self.llm = ChatBedrock(
            model_id=settings.LLM_MODEL_ID,
            client=self.session.client("bedrock-runtime"),
            model_kwargs={
                "temperature": settings.LLM_TEMPERATURE,
                "top_p": settings.LLM_TOP_P,
                "max_tokens": settings.LLM_MAX_TOKENS,
            },
        )

        logger.info(
            f"BedrockClient initialized with model: {settings.LLM_MODEL_ID}, "
            f"region: {settings.AWS_REGION}"
        )

    def invoke_claude(
        self,
        user_message: str,
        conversation_history: list[Message],
        system_prompt: str,
    ) -> str:
        """
        Invoke Claude Sonnet 4 with conversation history.

        Args:
            user_message: The current user message
            conversation_history: List of previous messages in the conversation
            system_prompt: System prompt to guide the model's behavior

        Returns:
            The model's response as a string

        Raises:
            Exception: If the Bedrock API call fails
        """
        try:
            # Convert conversation history to LangChain message format
            messages = self._format_conversation_history(
                conversation_history, system_prompt
            )

            # Add the current user message
            messages.append(HumanMessage(content=user_message))

            logger.debug(
                f"Invoking Claude with {len(messages)} messages "
                f"(including system prompt)"
            )

            # Invoke the model
            response = self.llm.invoke(messages)

            # Extract the response content
            response_text = response.content

            logger.info(
                f"Claude response generated successfully "
                f"({len(response_text)} characters)"
            )

            return response_text

        except Exception as e:
            logger.error(f"Failed to invoke Claude: {e}")
            raise

    def _format_conversation_history(
        self, conversation_history: list[Message], system_prompt: str
    ) -> list[SystemMessage | HumanMessage | AIMessage]:
        """
        Convert database Message models to LangChain message format.

        Args:
            conversation_history: List of Message models from database
            system_prompt: System prompt to prepend

        Returns:
            List of LangChain messages ready for Claude
        """
        messages: list[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=system_prompt)
        ]

        for msg in conversation_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                # System messages in history (rare) are converted to HumanMessage
                # to avoid multiple system prompts
                messages.append(HumanMessage(content=f"[System]: {msg.content}"))
            else:
                logger.warning(f"Unknown message role: {msg.role}, skipping")

        return messages


# Global singleton instance
_bedrock_client: BedrockClient | None = None


def get_bedrock_client() -> BedrockClient:
    """
    Get or create the global BedrockClient instance.

    Returns:
        The global BedrockClient singleton
    """
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
