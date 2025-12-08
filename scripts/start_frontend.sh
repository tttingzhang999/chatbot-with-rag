#!/bin/bash

# Start Gradio frontend

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
echo "Starting Gradio Frontend"
echo "=========================================="
echo "Backend API:  ${BACKEND_API_URL:-http://localhost:8000}"
echo "=========================================="
echo ""
echo "⚠️  Make sure FastAPI backend is running!"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Gradio app
python src/app.py
