"""
AWS Secrets Manager integration.

Provides utilities to fetch secrets from AWS Secrets Manager.
"""

import json
import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """AWS Secrets Manager client wrapper."""

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Secrets Manager client.

        Args:
            region_name: AWS region name
        """
        self.region_name = region_name
        self.client = boto3.client("secretsmanager", region_name=region_name)

    def get_secret(self, secret_name: str) -> dict:
        """
        Fetch secret from AWS Secrets Manager.

        Args:
            secret_name: Name or ARN of the secret

        Returns:
            Dictionary containing the secret data

        Raises:
            ClientError: If secret cannot be retrieved
            ValueError: If secret contains invalid JSON
        """
        try:
            logger.info(f"Fetching secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)

            # Parse the secret string as JSON
            if "SecretString" in response:
                secret_data = json.loads(response["SecretString"])
                logger.info(f"Successfully fetched secret: {secret_name}")
                return secret_data
            else:
                # Binary secrets are not supported in this implementation
                logger.error(f"Secret {secret_name} is binary, not supported")
                raise ValueError(f"Binary secrets are not supported: {secret_name}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Failed to fetch secret {secret_name}: {error_code}")

            if error_code == "ResourceNotFoundException":
                raise ValueError(f"Secret not found: {secret_name}") from e
            elif error_code == "InvalidRequestException":
                raise ValueError(f"Invalid request for secret: {secret_name}") from e
            elif error_code == "InvalidParameterException":
                raise ValueError(f"Invalid parameter for secret: {secret_name}") from e
            elif error_code == "DecryptionFailure":
                raise RuntimeError(f"Cannot decrypt secret {secret_name} using KMS") from e
            elif error_code == "InternalServiceError":
                raise RuntimeError(
                    f"Internal service error when fetching secret {secret_name}"
                ) from e
            else:
                raise

        except json.JSONDecodeError as e:
            logger.error(f"Secret {secret_name} contains invalid JSON")
            raise ValueError(f"Secret {secret_name} is not valid JSON: {str(e)}") from e

    def get_database_credentials(self, secret_name: str) -> dict:
        """
        Fetch database credentials from Secrets Manager.

        Args:
            secret_name: Name of the database secret

        Returns:
            Dictionary with keys: host, port, database, username, password

        Raises:
            ValueError: If required keys are missing from the secret
        """
        secret = self.get_secret(secret_name)

        required_keys = ["host", "port", "database", "username", "password"]
        missing_keys = [key for key in required_keys if key not in secret]

        if missing_keys:
            raise ValueError(f"Database secret missing required keys: {', '.join(missing_keys)}")

        return {
            "host": secret["host"],
            "port": int(secret["port"]),
            "database": secret["database"],
            "username": secret["username"],
            "password": secret["password"],
        }

    def get_app_secrets(self, secret_name: str) -> dict:
        """
        Fetch application secrets from Secrets Manager.

        Args:
            secret_name: Name of the app secrets

        Returns:
            Dictionary with application secrets (secret_key, algorithm, etc.)

        Raises:
            ValueError: If required keys are missing from the secret
        """
        secret = self.get_secret(secret_name)

        required_keys = ["secret_key"]
        missing_keys = [key for key in required_keys if key not in secret]

        if missing_keys:
            raise ValueError(f"App secret missing required keys: {', '.join(missing_keys)}")

        return secret

    def build_database_url(self, secret_name: str) -> str:
        """
        Build PostgreSQL connection URL from Secrets Manager secret.

        Args:
            secret_name: Name of the database secret

        Returns:
            PostgreSQL connection URL string
        """
        creds = self.get_database_credentials(secret_name)
        return (
            f"postgresql://{creds['username']}:{creds['password']}"
            f"@{creds['host']}:{creds['port']}/{creds['database']}"
        )


@lru_cache(maxsize=1)
def get_secrets_manager(region_name: str = "us-east-1") -> SecretsManager:
    """
    Get cached Secrets Manager instance.

    Args:
        region_name: AWS region name

    Returns:
        SecretsManager instance
    """
    return SecretsManager(region_name=region_name)


def load_database_url_from_secrets(secret_name: str, region_name: str = "us-east-1") -> str:
    """
    Load database URL from AWS Secrets Manager.

    This is a convenience function for use in configuration loading.

    Args:
        secret_name: Name of the database secret
        region_name: AWS region name

    Returns:
        PostgreSQL connection URL string

    Example:
        >>> from src.core.secrets import load_database_url_from_secrets
        >>> db_url = load_database_url_from_secrets("hr-chatbot/database")
    """
    sm = get_secrets_manager(region_name)
    return sm.build_database_url(secret_name)


def load_secret_key_from_secrets(secret_name: str, region_name: str = "us-east-1") -> str:
    """
    Load SECRET_KEY from AWS Secrets Manager.

    Args:
        secret_name: Name of the app secrets
        region_name: AWS region name

    Returns:
        SECRET_KEY string

    Example:
        >>> from src.core.secrets import load_secret_key_from_secrets
        >>> secret_key = load_secret_key_from_secrets("hr-chatbot/app-secrets")
    """
    sm = get_secrets_manager(region_name)
    secrets = sm.get_app_secrets(secret_name)
    return secrets["secret_key"]
