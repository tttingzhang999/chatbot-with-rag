#!/bin/bash
# 啟動本地 FastAPI 後端 (with hot-reload)
# Requires aws-vault for AWS authentication
#
# Usage:
#   ./start-backend.sh <aws-profile>
#
# Examples:
#   ./start-backend.sh default
#   ./start-backend.sh hr-chatbot-dev

set -e

# Check if AWS profile is provided
if [ -z "$1" ]; then
    echo "❌ Error: AWS profile is required"
    echo ""
    echo "Usage:"
    echo "  ./start-backend.sh <aws-profile>"
    echo ""
    echo "Examples:"
    echo "  ./start-backend.sh default"
    echo "  ./start-backend.sh hr-chatbot-dev"
    echo ""
    echo "Setup aws-vault first if you haven't:"
    echo "  brew install aws-vault"
    echo "  aws-vault add <profile-name>"
    exit 1
fi

AWS_PROFILE="$1"

# Check if aws-vault is installed
if ! command -v aws-vault &> /dev/null; then
    echo "❌ Error: aws-vault is not installed"
    echo ""
    echo "Please install aws-vault first:"
    echo "  macOS:   brew install aws-vault"
    echo "  Linux:   See https://github.com/99designs/aws-vault#installing"
    exit 1
fi

# Change to backend directory
cd "$(dirname "$0")/../../apps/backend" || exit

# Load .env from root (for non-AWS settings like DATABASE_URL)
if [ -f "../../.env" ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' ../../.env | xargs)
fi

echo "=========================================="
echo "Starting FastAPI Backend (Local Development)"
echo "=========================================="
echo "API:  http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Mode: Hot-reload enabled"
echo "Auth: aws-vault (profile: $AWS_PROFILE)"
echo "=========================================="
echo ""

# Start uvicorn with hot-reload via aws-vault
exec aws-vault exec "$AWS_PROFILE" -- uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
