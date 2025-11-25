# Local Development Guide

This guide explains how to run the HR Chatbot locally for development, without AWS services.

## Overview

The local development setup includes:
- **FastAPI Backend** (port 8000): REST API for chat and authentication
- **Gradio Frontend** (port 7860): Web interface for users
- **PostgreSQL**: Local database for storing conversations

Currently, the chatbot uses a simple **echo response** instead of LLM, which will be replaced with AWS Bedrock (Claude Sonnet 4) in production.

## Prerequisites

1. **Python 3.11+** installed
2. **PostgreSQL** running locally
3. **uv** package manager installed
4. Database created and configured

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
nano .env  # Edit with your local PostgreSQL URL
```

Example `.env` for local development:

```bash
DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/hr_chatbot

# AWS settings (not used locally, but keep for future)
AWS_REGION=us-east-1
DOCUMENT_BUCKET=your-bucket
LLM_MODEL_ID=anthropic.claude-sonnet-4
EMBEDDING_MODEL_ID=cohere.embed-v4
```

### 2. Initialize Database

```bash
# Create database
createdb hr_chatbot

# Enable extensions and create tables
./scripts/init_db.sh

# Or manually:
python -m src.db.init_db
```

### 3. Start Backend Server

In one terminal:

```bash
# Using script
./scripts/start_backend.sh

# Or manually:
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

### 4. Start Frontend

In another terminal:

```bash
# Using script
./scripts/start_frontend.sh

# Or manually:
python src/app.py
```

The Gradio interface will be available at:
- http://localhost:7860

## Testing

### Manual Testing

1. Open http://localhost:7860 in your browser
2. Login with any username (e.g., "test_user")
3. Start chatting - you'll see echo responses
4. Try creating multiple conversations
5. Upload files (they'll be received but not processed yet)

### API Testing

Test the API endpoints directly:

```bash
# Run test script
python scripts/test_api.py

# Or manually with curl
curl http://localhost:8000/health

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user"}'

curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{"message": "Hello!"}'
```

### Running Tests

```bash
# Run pytest (when tests are implemented)
pytest

# With coverage
pytest --cov=src
```

## Project Structure

```
hr-chatbot/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py       # Login endpoints
│   │   │   ├── chat.py       # Chat endpoints
│   │   │   └── upload.py     # File upload
│   │   └── deps.py           # Dependencies (DB session, auth)
│   ├── services/
│   │   ├── auth_service.py   # Authentication logic
│   │   └── chat_service.py   # Chat logic (echo + DB)
│   ├── models/               # SQLAlchemy models
│   ├── db/                   # Database connection
│   ├── core/                 # Configuration
│   ├── main.py               # FastAPI app
│   └── app.py                # Gradio frontend
├── scripts/
│   ├── init_db.sh            # Initialize database
│   ├── start_backend.sh      # Start FastAPI
│   ├── start_frontend.sh     # Start Gradio
│   └── test_api.py           # API tests
└── docs/                     # Documentation
```

## API Endpoints

### Authentication

- `POST /auth/login` - Login with username
  ```json
  {"username": "test_user"}
  ```

### Chat

- `POST /chat/message` - Send message and get response
  - Header: `X-User-Id: <user_id>`
  - Body: `{"message": "...", "conversation_id": "..."}`

- `GET /chat/conversations` - Get user's conversations
  - Header: `X-User-Id: <user_id>`

- `GET /chat/conversations/{id}` - Get conversation history
  - Header: `X-User-Id: <user_id>`

- `POST /chat/conversations` - Create new conversation
  - Header: `X-User-Id: <user_id>`

- `DELETE /chat/conversations/{id}` - Delete conversation
  - Header: `X-User-Id: <user_id>`

### Upload

- `POST /upload/document` - Upload document (received but not processed)
  - Header: `X-User-Id: <user_id>`
  - Body: multipart/form-data with file

## Database Schema

Currently using these tables:

### conversations
- `id`: UUID primary key
- `user_id`: User identifier
- `title`: Conversation title
- `created_at`, `updated_at`: Timestamps
- `metadata`: JSONB for flexible data

### messages
- `id`: UUID primary key
- `conversation_id`: Foreign key to conversations
- `role`: "user" or "assistant"
- `content`: Message text
- `retrieved_chunks`: JSONB (empty for now)
- `created_at`: Timestamp

### Not yet used
- `documents`: For uploaded files (future)
- `document_chunks`: For RAG chunks (future)

## Current Limitations

### What's Working
✅ User authentication (simple, username-only)
✅ Multi-turn conversations
✅ Conversation history
✅ File upload (receives files)
✅ Database persistence

### What's Not Yet Implemented
❌ LLM integration (using echo instead)
❌ Document processing (files uploaded but not processed)
❌ RAG / Hybrid search
❌ AWS Bedrock integration
❌ Vector embeddings
❌ BM25 search

## Development Workflow

### Making Changes

1. **Backend changes**: Edit files in `src/api/` or `src/services/`
   - FastAPI auto-reloads on file changes
   - Test at http://localhost:8000/docs

2. **Frontend changes**: Edit `src/app.py`
   - Restart Gradio to see changes
   - Or enable auto-reload in Gradio

3. **Database changes**: Edit models in `src/models/`
   - Create migration: `alembic revision --autogenerate -m "description"`
   - Apply migration: `alembic upgrade head`

### Code Quality

```bash
# Format and lint
ruff format .
ruff check --fix .

# Pre-commit will run automatically on commit
git commit -m "your message"
```

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Make sure you installed the package in editable mode:
```bash
uv pip install -e ".[dev]"
```

### Database connection error

**Error**: `could not connect to server: Connection refused`

**Solution**: Make sure PostgreSQL is running:
```bash
# Check status
pg_isready

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@15
```

### Frontend can't connect to backend

**Error**: `Cannot connect to API`

**Solution**: Make sure backend is running on port 8000:
```bash
curl http://localhost:8000/health
```

### Import errors

**Error**: `cannot import name 'xxx' from 'src.xxx'`

**Solution**: Check that all `__init__.py` files exist and imports are correct.

## Next Steps

Once local development is working, you can:

1. **Integrate LLM**: Replace echo in `chat_service.py` with LLM calls
2. **Add document processing**: Implement chunking and embedding generation
3. **Implement RAG**: Add hybrid search (semantic + BM25)
4. **AWS integration**: Connect to Bedrock, S3, Aurora
5. **Deploy to Lambda**: Containerize and deploy to AWS

## Useful Commands

```bash
# Start everything
./scripts/init_db.sh
./scripts/start_backend.sh  # Terminal 1
./scripts/start_frontend.sh # Terminal 2

# Test API
python scripts/test_api.py

# Database management
psql -d hr_chatbot
\dt  # List tables
\d+ conversations  # Describe table

# Code quality
ruff check .
ruff format .
pre-commit run --all-files

# View logs
# Backend logs are in terminal where you started it
# Frontend logs in Gradio terminal
```

## Resources

- FastAPI docs: https://fastapi.tiangolo.com/
- Gradio docs: https://gradio.app/docs/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Project README: [../README.md](../README.md)
- Architecture docs: [../architecture.md](../architecture.md)
