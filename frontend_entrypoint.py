"""
Entry point for running Gradio frontend in AWS App Runner.

This module initializes logging, loads environment variables, and launches the Gradio
application using Gradio's native launch() method (appropriate for containerized deployment).
"""

import logging
import sys
from pathlib import Path

# Ensure src module can be imported from any working directory
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging BEFORE any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entry point for the Gradio frontend.

    Handles environment setup, logging, and Gradio application launch.
    """
    try:
        logger.info("=" * 70)
        logger.info("Starting HR Chatbot Gradio Frontend")
        logger.info("=" * 70)

        # Import configuration and application (after logging is configured)
        from src.app import demo
        from src.core.config import settings

        # Log configuration details
        logger.info(f"Gradio Host: {settings.GRADIO_HOST}")
        logger.info(f"Gradio Port: {settings.GRADIO_PORT}")
        logger.info(f"Backend API:  {settings.BACKEND_API_URL}")
        logger.info(f"Debug Mode:   {settings.DEBUG}")
        logger.info("=" * 70)
        logger.info("Launching Gradio application...")
        logger.info("=" * 70)

        # Launch using Gradio's native method (appropriate for App Runner/containers)
        demo.launch(
            server_name=settings.GRADIO_HOST,
            server_port=settings.GRADIO_PORT,
            share=False,
            show_error=True,
            show_api=True,
        )

    except Exception as e:
        logger.error("=" * 70)
        logger.error("FATAL ERROR: Failed to start Gradio frontend")
        logger.error("=" * 70)
        logger.exception(e)
        logger.error("=" * 70)
        logger.error("Troubleshooting tips:")
        logger.error("1. Verify BACKEND_API_URL is set correctly in .env")
        logger.error("2. Ensure all environment variables are properly configured")
        logger.error("3. Check container logs for detailed error messages")
        logger.error("4. Run locally first: python src/app.py")
        logger.error("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
