#!/bin/bash
# Backend container startup script (Production Mode)
# Runs inside the backend Docker container
# NO hot-reload - simulates production behavior

set -e

echo "=========================================="
echo "Starting Backend (Production Mode)"
echo "=========================================="

# Run database migrations
echo "Running database migrations..."
cd /var/task
python -m alembic upgrade head
echo "✅ Migrations completed"

# Start uvicorn WITHOUT --reload
echo ""
echo "Starting FastAPI server..."
echo "API:  http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Mode: Production (no hot-reload)"
echo "=========================================="

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
