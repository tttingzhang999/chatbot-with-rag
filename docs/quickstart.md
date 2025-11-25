# Quick Start Guide

This guide will help you set up the HR Chatbot development environment using uv, ruff, and pre-commit.

> **🚀 Want to start coding right away?** Check out [Local Development Guide](./local_development.md) for running the app locally without AWS services.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ (or AWS Aurora PostgreSQL access)
- AWS credentials configured
- Git

## 1. Install uv

uv is a fast Python package manager. Install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

## 2. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd hr-chatbot

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -e ".[dev]"
```

This will install all required dependencies defined in `pyproject.toml`, including:
- Core dependencies (FastAPI, SQLAlchemy, etc.)
- Development dependencies (ruff, pre-commit, pytest)

## 3. Configure Pre-commit Hooks

Pre-commit hooks ensure code quality before each commit:

```bash
# Install pre-commit hooks
pre-commit install

# (Optional) Run on all files to verify setup
pre-commit run --all-files
```

The pre-commit hooks will automatically:
- Run ruff linter and formatter
- Check for common issues (large files, merge conflicts, etc.)
- Run security checks with bandit
- Format markdown files

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example env file (if available)
cp .env.example .env

# Edit the .env file
nano .env
```

Add the following configuration:

```bash
# Application
DEBUG=true

# Database (local development)
DATABASE_URL=postgresql://postgres:password@localhost:5432/hr_chatbot

# Or use AWS Secrets Manager for Aurora
# DB_SECRET_NAME=hr-chatbot/db-credentials
# AWS_REGION=us-east-1

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile-name

# S3
DOCUMENT_BUCKET=your-s3-bucket-name

# Bedrock Models
LLM_MODEL_ID=anthropic.claude-sonnet-4
EMBEDDING_MODEL_ID=cohere.embed-v4

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_CHUNKS=10
SEMANTIC_SEARCH_RATIO=0.5
EMBEDDING_DIMENSION=1024
```

## 5. Setup Database

### Local PostgreSQL

```bash
# Create database
createdb hr_chatbot

# Enable extensions
psql -d hr_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -d hr_chatbot -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# Initialize database schema
python -m src.db.init_db
```

### Or use Alembic for migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

For detailed database setup instructions, see [`docs/setup_database.md`](./setup_database.md).

## 6. Verify Setup

Test that everything is working:

```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Run tests (when available)
pytest

# Test database connection
python -c "from src.db import engine; print(engine.execute('SELECT 1').scalar())"
```

## 7. Development Workflow

### Code Quality

The project uses ruff for linting and formatting:

```bash
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Or let pre-commit handle it automatically on commit
git commit -m "your message"
```

### Running the Application

```bash
# Start FastAPI server (when implemented)
uvicorn src.main:app --reload

# Or start Gradio interface (when implemented)
python -m src.app
```

### Working with Database

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding New Dependencies

```bash
# Add a new dependency
uv pip install <package-name>

# Update pyproject.toml manually, then sync
uv pip install -e ".[dev]"

# For development dependencies, add to [project.optional-dependencies] in pyproject.toml
```

## 8. Project Structure

```
hr-chatbot/
├── src/
│   ├── core/              # Configuration and settings
│   ├── db/                # Database connection and initialization
│   ├── models/            # SQLAlchemy models
│   ├── api/               # FastAPI routes (to be implemented)
│   ├── services/          # Business logic (to be implemented)
│   ├── document_processor/ # Document processing pipeline (to be implemented)
│   └── retrieval/         # Hybrid search implementation (to be implemented)
├── alembic/               # Database migrations
├── docs/                  # Documentation
├── tests/                 # Test files (to be implemented)
├── .env                   # Environment variables (not in git)
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── pyproject.toml         # Project configuration and dependencies
└── README.md
```

## Common Commands

### Package Management

```bash
# Install/update dependencies
uv pip install -e ".[dev]"

# Add a new package
uv pip install <package>

# List installed packages
uv pip list

# Generate requirements.txt (if needed)
uv pip freeze > requirements.txt
```

### Code Quality

```bash
# Lint check
ruff check .

# Lint with auto-fix
ruff check --fix .

# Format code
ruff format .

# Run pre-commit on all files
pre-commit run --all-files

# Update pre-commit hooks
pre-commit autoupdate
```

### Database

```bash
# Initialize database
python -m src.db.init_db

# Create migration
alembic revision --autogenerate -m "message"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_models.py

# Run tests matching pattern
pytest -k "test_document"
```

## Next Steps

1. Review the [architecture documentation](../architecture.md)
2. Read the [database schema documentation](./database_schema.md)
3. Start implementing the document processor module
4. Implement the hybrid search retrieval system
5. Build the FastAPI endpoints
6. Create the Gradio frontend

## Troubleshooting

### uv command not found

Restart your terminal or manually add uv to PATH:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

### Pre-commit hooks failing

Run auto-fix and try again:

```bash
ruff check --fix .
ruff format .
git add -u
git commit -m "your message"
```

### Database connection errors

Verify your `.env` file has correct DATABASE_URL and PostgreSQL is running:

```bash
psql -d hr_chatbot -c "SELECT 1;"
```

### Import errors

Make sure the package is installed in editable mode:

```bash
uv pip install -e ".[dev]"
```

## Resources

- [uv documentation](https://github.com/astral-sh/uv)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [pre-commit documentation](https://pre-commit.com/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/)
- [Alembic documentation](https://alembic.sqlalchemy.org/)
