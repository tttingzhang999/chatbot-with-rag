#!/bin/bash

# Start FastAPI backend server with AWS Vault credentials
# This script requires aws-vault to be configured

# Change to project root directory
cd "$(dirname "$0")/.." || exit

# Load all environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    # Export all non-comment, non-empty lines from .env
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found!"
fi

# Check if AWS_REGION is set
if [ -z "$AWS_REGION" ]; then
    echo "Warning: AWS_REGION not set, using default: us-east-1"
    export AWS_REGION=us-east-1
fi

# Use AWS_PROFILE from .env or ask user
if [ -z "$AWS_PROFILE" ]; then
    echo "AWS_PROFILE not found in .env file"
    echo "Please enter your AWS profile name:"
    read AWS_PROFILE
fi

echo "=========================================="
echo "Starting FastAPI backend with AWS Vault"
echo "=========================================="
echo "AWS Profile: $AWS_PROFILE"
echo "AWS Region:  $AWS_REGION"
echo "Backend URL: http://localhost:${UVICORN_PORT:-8000}"
echo "API Docs:    http://localhost:${UVICORN_PORT:-8000}/docs"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start uvicorn server with aws-vault
# AWS_REGION must be exported for aws-vault to work
export AWS_REGION
aws-vault exec "$AWS_PROFILE" -- .venv/bin/python -m uvicorn src.main:app --reload
