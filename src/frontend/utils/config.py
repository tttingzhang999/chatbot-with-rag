"""
Frontend-specific configuration.
"""

from pathlib import Path

from src.core.config import settings

# Paths / configuration
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent.parent / settings.ASSETS_DIR
BOT_AVATAR_PATH = ASSETS_DIR / settings.BOT_AVATAR_FILENAME
BOT_AVATAR_IMAGE = str(BOT_AVATAR_PATH) if BOT_AVATAR_PATH.exists() else None
