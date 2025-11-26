#!/bin/bash

# Start FastAPI backend server (local development without AWS)

# Change to project root directory
cd "$(dirname "$0")/.." || exit

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Starting FastAPI backend (Local Mode)"
echo "=========================================="
echo "Backend URL: http://localhost:${UVICORN_PORT:-8000}"
echo "API Docs:    http://localhost:${UVICORN_PORT:-8000}/docs"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start uvicorn server (config from settings)
python -m uvicorn src.main:app --reload
