#!/usr/bin/env python3
"""
Generate a SECRET_KEY for JWT token signing.
"""

import secrets

if __name__ == "__main__":
    secret_key = secrets.token_hex(32)
    print("Generated SECRET_KEY:")
    print(secret_key)
    print()
    print("Add this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
