# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-25

### Added

#### Database & Models
- PostgreSQL database schema with 5 tables (users, documents, document_chunks, conversations, messages)
- SQLAlchemy ORM models for all tables with proper relationships
- pgvector extension v0.8.1 support for vector embeddings (1024 dimensions)
- pg_trgm extension v1.6 for full-text search (BM25)
- Alembic database migration configuration with proper extension management
- Database initialization script (`src/db/init_db.py`)
- Initial migration: `c7b3cd923558_initial_schema_with_users_documents_conversations`
- IVFFlat vector index for efficient cosine similarity search
- GIN index for full-text search on tsvector column

#### Backend API (FastAPI)
- FastAPI application structure (`src/main.py`)
- Authentication routes with JWT support:
  - `POST /auth/register` - User registration with email validation
  - `POST /auth/login` - User login with JWT token generation
- Chat routes for conversation management:
  - `POST /chat/message` - Send message and get response
  - `GET /chat/conversations` - Get user's conversation list
  - `GET /chat/conversations/{id}` - Get conversation history
  - `POST /chat/conversations` - Create new conversation
  - `DELETE /chat/conversations/{id}` - Delete conversation
- File upload route (`POST /upload/document`)
- API dependency injection system (`src/api/deps.py`)
- Health check endpoint (`/health`)
- Auto-generated OpenAPI documentation (`/docs`)
- CORS middleware configuration

#### Security & Authentication
- JWT-based authentication with python-jose
- Password hashing with passlib and bcrypt
- Email validation with email-validator
- Secure SECRET_KEY configuration from environment variables
- Token-based API access control

#### Service Layer
- `chat_service.py` - Chat logic with echo responses (placeholder for LLM)
  - Conversation management
  - Message persistence
  - Conversation history retrieval
- `auth_service.py` - Simple user validation

#### Frontend (Gradio)
- Gradio web interface (`src/app.py`)
- Login page with username input
- Chat interface with:
  - Multi-turn conversation display
  - Message input and send functionality
  - New conversation button
  - Conversation history sidebar
  - File upload component
- Real-time API communication with FastAPI backend

#### Development Tools & Configuration
- `pyproject.toml` with uv package management and hatchling build backend
- Hatch build configuration for proper package structure
- ruff configuration for linting and formatting
- pre-commit hooks configuration
- Shell scripts for development:
  - `scripts/init_db.sh` - Initialize database
  - `scripts/start_backend.sh` - Start FastAPI server
  - `scripts/start_frontend.sh` - Start Gradio frontend
  - `scripts/test_api.py` - API endpoint tests
- `.env.example` - Environment variables template with SECRET_KEY generation guide
- `.env` configuration with secure SECRET_KEY (not committed to git)
- `.gitignore` - Git ignore configuration
- PostgreSQL 18 local development setup with Homebrew
- psql command-line tools configured in PATH

#### Documentation
- `docs/database_schema.md` - Detailed database schema documentation
- `docs/database_erd.md` - Entity-relationship diagram and examples
- `docs/setup_database.md` - Database setup guide
- `docs/quickstart.md` - Quick start guide
- `docs/local_development.md` - Comprehensive local development guide
- `docs/implementation_status.md` - Current implementation status
- `CLAUDE.md` - Guidance for Claude Code
- Updated `README.md` with Phase 0 completion status
- Updated `architecture.md` with fixed Markdown list formatting

### Changed
- Migrated from requirements.txt to pyproject.toml for dependency management
- Updated project structure to support FastAPI + Gradio architecture
- Renamed `metadata` columns to `extra_metadata` to avoid SQLAlchemy reserved keyword conflict
- Updated Alembic env.py to use `text()` wrapper for raw SQL execution (SQLAlchemy 2.0 compatibility)

### Fixed
- Fixed pyproject.toml missing hatch build configuration causing `uv sync` to fail
- Fixed Alembic migration missing pgvector import
- Fixed database connection configuration to read from .env securely (no plaintext passwords in alembic.ini)
- Added missing dependencies: email-validator for Pydantic email validation

### Technical Details
- Backend runs on port 8000 (FastAPI)
- Frontend runs on port 7860 (Gradio)
- Local PostgreSQL 18 database on port 5432
  - Database: `hr_chatbot`
  - User: `postgres` (password configured via .env)
  - Extensions: pgvector v0.8.1, pg_trgm v1.6
- Database schema initialized with Alembic migration
- Secure configuration: DATABASE_URL and SECRET_KEY read from .env file
- Echo responses for chat (LLM integration pending)
- File uploads accepted but not processed (document processing pending)

### Database Setup Completed
- ✅ PostgreSQL 18 installed via Homebrew
- ✅ pgvector 0.8.1 extension installed
- ✅ Local database `hr_chatbot` created
- ✅ All tables created with proper indexes:
  - IVFFlat index for vector similarity search (cosine distance)
  - GIN index for full-text search (tsvector)
  - B-tree indexes for foreign keys and frequently queried columns
- ✅ Database connection secure (credentials in .env, not in code)

## [0.0.1] - 2025-11-25

### Added

- Initialize project
- Add README.md, CHANGELOG.md, VERSION.md, architecture.md