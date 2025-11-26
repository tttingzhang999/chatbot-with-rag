"""
Password hashing and verification utilities.

Uses SHA256 pre-hashing + bcrypt to support passwords of any length
while maintaining security against brute-force attacks.
"""

import hashlib

import bcrypt


def _prehash_password(password: str) -> bytes:
    """
    Pre-hash password using SHA256 to avoid bcrypt's 72-byte limit.

    This allows passwords of any length to be securely hashed.
    The SHA256 output is always 64 hex characters (32 bytes),
    well under bcrypt's 72-byte limit.

    Args:
        password: Plain text password of any length

    Returns:
        bytes: SHA256 hex digest encoded as UTF-8 bytes
    """
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return sha256_hash.encode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Uses SHA256 pre-hashing before bcrypt verification to support
    passwords of any length.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database (bcrypt hash string)

    Returns:
        bool: True if password matches, False otherwise
    """
    prehashed = _prehash_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(prehashed, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA256 + bcrypt.

    Uses SHA256 pre-hashing before bcrypt to support passwords of any length,
    avoiding bcrypt's 72-byte limit while maintaining security.

    Args:
        password: Plain text password of any length

    Returns:
        str: Hashed password (bcrypt hash of SHA256 digest)
    """
    prehashed = _prehash_password(password)
    # Generate salt and hash the pre-hashed password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prehashed, salt)
    return hashed.decode("utf-8")
