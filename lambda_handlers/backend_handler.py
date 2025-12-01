"""
AWS Lambda handler for FastAPI backend.
"""

from mangum import Mangum

from src.main import app

# Create Mangum adapter for Lambda
handler = Mangum(app, lifespan="off")
