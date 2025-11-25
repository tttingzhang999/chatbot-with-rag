#!/bin/bash

# Initialize database

echo "Initializing database..."
echo ""

cd "$(dirname "$0")/.." || exit

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run database initialization
python -m src.db.init_db

echo ""
echo "Database initialized successfully!"
echo "You can now start the backend and frontend servers."
