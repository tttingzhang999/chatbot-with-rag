"""
Entry point for running FastAPI backend in AWS Lambda.

This module serves as the Lambda handler entry point, using Mangum to adapt
the FastAPI application for AWS Lambda runtime.
"""

import logging
import sys
from pathlib import Path

from mangum import Mangum

from src.main import app

# Ensure src module can be imported from any working directory
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create Mangum adapter for Lambda
handler = Mangum(app, lifespan="off")
