#!/bin/bash

# Start Gradio frontend

echo "Starting Gradio frontend on http://localhost:7860"
echo "Make sure FastAPI backend is running on http://localhost:8000"
echo ""

cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Gradio app
python src/app.py
