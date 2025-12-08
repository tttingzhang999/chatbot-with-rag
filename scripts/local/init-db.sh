#!/bin/bash
# 初始化本機資料庫
# Runs Alembic migrations on local PostgreSQL

set -e

# Change to backend directory
cd "$(dirname "$0")/../../apps/backend" || exit

echo "=========================================="
echo "Initializing Local Database"
echo "=========================================="
echo "Running Alembic migrations..."

# Run migrations
uv run alembic upgrade head

echo ""
echo "✅ Database initialized successfully"
echo "=========================================="
