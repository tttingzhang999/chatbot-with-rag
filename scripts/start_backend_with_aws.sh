#!/bin/bash

# Start FastAPI backend server with AWS Vault credentials
# This script requires aws-vault to be configured

# Check if AWS_PROFILE is set in .env
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep AWS_PROFILE | xargs)
fi

# Use AWS_PROFILE from .env or ask user
if [ -z "$AWS_PROFILE" ]; then
    echo "AWS_PROFILE not found in .env file"
    echo "Please enter your AWS profile name:"
    read AWS_PROFILE
fi

echo "Starting FastAPI backend with AWS Vault profile: $AWS_PROFILE"
echo "Backend will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""

cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start uvicorn server with aws-vault
# Use full path to python to avoid PATH issues with aws-vault
aws-vault exec "$AWS_PROFILE" -- .venv/bin/python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
