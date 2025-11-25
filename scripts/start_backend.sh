#!/bin/bash

# Start FastAPI backend server

echo "Starting FastAPI backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""

cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start uvicorn server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
