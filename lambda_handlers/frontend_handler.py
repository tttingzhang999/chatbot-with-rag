"""
AWS Lambda handler for Gradio frontend.
"""

from mangum import Mangum

from src.app import demo

# Create Mangum adapter for Lambda
handler = Mangum(demo, lifespan="off")
