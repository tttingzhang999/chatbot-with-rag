"""
Amazon Bedrock client for LLM and embedding operations.

This module provides a wrapper around AWS Bedrock services for:
- Claude Sonnet 4 LLM invocations
- Cohere Embed v4 embedding generation
- Conversation history management
- Error handling and retries
"""

import json
import logging
import time

import boto3
from botocore.config import Config
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

        # Configure retry strategy with exponential backoff for throttling
        retry_config = Config(
            retries={
                "max_attempts": 8,  # Increased from default 4
                "mode": "adaptive",  # Adaptive mode adjusts retry behavior based on success/failure
            },
            # Add connection timeout and read timeout
            connect_timeout=30,
            read_timeout=60,
        )

        # Initialize bedrock-runtime client for embeddings with retry config
        self.bedrock_runtime = self.session.client(
            "bedrock-runtime",
            config=retry_config,
        )

        # Initialize ChatBedrock for Claude Sonnet 4
        self.llm = ChatBedrock(
            model_id=settings.LLM_MODEL_ID,
            client=self.bedrock_runtime,
            model_kwargs={
                "temperature": settings.LLM_TEMPERATURE,
                "top_p": settings.LLM_TOP_P,
                "max_tokens": settings.LLM_MAX_TOKENS,
            },
        )

        logger.info(
            f"BedrockClient initialized with LLM: {settings.LLM_MODEL_ID}, "
            f"Embedding: {settings.EMBEDDING_MODEL_ID}, region: {settings.AWS_REGION}"
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
            messages = self._format_conversation_history(conversation_history, system_prompt)

            # Add the current user message
            messages.append(HumanMessage(content=user_message))

            logger.debug(f"Invoking Claude with {len(messages)} messages (including system prompt)")

            # Invoke the model
            response = self.llm.invoke(messages)

            # Extract the response content
            response_text = response.content

            logger.info(f"Claude response generated successfully ({len(response_text)} characters)")

            return response_text

        except Exception as e:
            logger.error(f"Failed to invoke Claude: {e}")
            raise

    def generate_embeddings(
        self,
        texts: list[str],
        input_type: str = "search_document",
        batch_size: int = 96,
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using Cohere Embed v4.

        Args:
            texts: List of text strings to embed
            input_type: Type of input text. Options:
                - "search_document": For document chunks (default)
                - "search_query": For search queries
            batch_size: Maximum number of texts to process in one API call (max 96)

        Returns:
            List of embedding vectors (1024 dimensions each)

        Raises:
            Exception: If the Bedrock API call fails
        """
        if not texts:
            return []

        # Cohere Embed v4 supports up to 96 texts per request
        batch_size = min(batch_size, 96)
        all_embeddings = []

        try:
            # Process in batches to avoid API limits
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(texts) + batch_size - 1) // batch_size

                logger.debug(
                    f"Generating embeddings for batch {batch_num}/{total_batches} "
                    f"({len(batch)} texts)"
                )

                # Add delay between batches to avoid rate limiting (except for first batch)
                if i > 0:
                    delay = 0.5  # 500ms delay between batches
                    logger.debug(f"Adding {delay}s delay to avoid throttling")
                    time.sleep(delay)

                # Prepare request body for Cohere Embed v4
                request_body = {
                    "texts": batch,
                    "input_type": input_type,
                    "embedding_types": ["float"],
                }

                # Invoke Bedrock model with retry handling
                try:
                    response = self.bedrock_runtime.invoke_model(
                        modelId=settings.EMBEDDING_MODEL_ID,
                        contentType="application/json",
                        accept="application/json",
                        body=json.dumps(request_body),
                    )
                except Exception as e:
                    # If throttling occurs even with retries, log and re-raise
                    if "ThrottlingException" in str(e):
                        logger.warning(
                            f"Throttling detected on batch {batch_num}/{total_batches}, "
                            "retries exhausted"
                        )
                    raise

                # Parse response
                response_body = json.loads(response["body"].read())

                # Extract embeddings from response
                # Cohere Embed v4 returns embeddings in 'embeddings' field
                batch_embeddings = response_body.get("embeddings", {}).get("float", [])

                if not batch_embeddings:
                    raise ValueError("No embeddings returned from Bedrock API")

                all_embeddings.extend(batch_embeddings)

            logger.info(
                f"Generated {len(all_embeddings)} embeddings "
                f"({settings.EMBEDDING_DIMENSION} dimensions each)"
            )

            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector (1024 dimensions)

        Raises:
            Exception: If the Bedrock API call fails
        """
        embeddings = self.generate_embeddings([query], input_type="search_query")
        return embeddings[0] if embeddings else []

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
