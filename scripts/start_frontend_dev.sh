#!/bin/bash

# Start Gradio frontend with hot reload (development mode)

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
echo "Starting Gradio Frontend (Dev Mode)"
echo "=========================================="
echo "Frontend URL: http://localhost:${GRADIO_PORT:-7860}"
echo "Backend API:  ${BACKEND_API_URL:-http://localhost:8000}"
echo "Mode:         🔥 Hot Reload Enabled"
echo "=========================================="
echo ""
echo "⚠️  Make sure FastAPI backend is running!"
echo "💡 Code changes will auto-reload"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Gradio app with hot reload using gradio command
gradio src/app.py --demo-name=demo
