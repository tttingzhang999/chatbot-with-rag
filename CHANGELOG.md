# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] 2025-12-03 - AWS Terraform Infrastructure: VPC, DB, Lambda, App Runner

### Added

- **Terraform deployments for AWS infrastructure:**
  - All-in-one IaC for end-to-end deployment on AWS, including VPC setup, public/private subnets, networking (security groups, endpoints), RDS Aurora PostgreSQL, Lambda backend, App Runner frontend, S3, and required Secrets Manager entries.
  - `main.tf` with provider and backend config, supports cross-account Route 53 management and ACM certificate for App Runner domain.
  - `vpc.tf`, `database.tf`, `lambda.tf`, `apprunner.tf`, `route53.tf`, `outputs.tf`, `s3.tf`, `secret.tf` — modular Terraform configs for all major infra resources now included.
- **App Runner TLS/Domain automation:**
  - Automatic ACM certificate creation and DNS validation for App Runner HTTPS custom domain (`ting-hr-chatbot.goingcloud.ai`) using Route 53 in separate AWS account.
  - Output variables for validation, DNS targets, and troubleshooting.
- **Lambda/Container deployment clarifications:**
  - All environments, roles, networking and image refs for Lambda and App Runner now managed via Terraform variables and outputs.
  - Includes automation notes for image versioning and role ARNs.

### Changed

- **uv.lock / requirements updates:**
  - Added `mangum` (`0.19.0`) to dependencies for Lambda ASGI compatibility.

### Migration & Usage Notes

- See `/terraform/README.md` and top of each Terraform module for usage, required AWS profiles, and prerequisites.
- ECR image tags and referenced role ARNs must match your CI or manual build flow.
- Some manual steps may be required after first App Runner custom domain deploy (validation records).
- Example DNS zone is hardcoded to GoingCloud test account and should be replaced for production use.

### See Also

- All new Terraform configs under `/terraform`
- aws_deployment_guide.md for Lambda, App Runner, ACM, and DNS troubleshooting

## [0.7.0] 2025-12-02 - AWS Cloud Deployment: Lambda, API Gateway, App Runner

### Added

- **Production-grade AWS deployment:** End-to-end support for deploying backend (FastAPI) as a Lambda container via API Gateway and deploying frontend (Gradio) to AWS App Runner, complete with all required environment variables, security, and networking considerations.
- **Comprehensive AWS deployment guide:** New deployment troubleshooting guide, linked and included as in-code and documentation comments, covering common issues (health checks, port configuration, container platform, Lambda cold/warm starts) for AWS Lambda and App Runner.
- **AppRunner & Lambda Docker best practices:** Added step-by-step instructions for multi-architecture builds, correct manifest/media types for ECR/Lambda, optimal health check & port configs for App Runner.
- **Automatic / secure environment loading in scripts:** All startup and deployment scripts (backend/frontend AWS/local) upgraded to load environment from `.env`, robustly handle missing or overridden variables (`UVICORN_PORT`, `GRADIO_PORT`, `AWS_PROFILE`, etc), and properly fall back to AWS/AppRunner-provided envs.
- **Safer upload dir handling:** Upload path for file storage now always falls back to `/tmp` if running on Lambda or read-only filesystems.
- **Updated `.env.example`:** All config (including optional API/meta/CORS/limits) now fully documented for clarity in cloud, CI, or local.
- **App Runner/Lambda deployment configs, build scripts, and troubleshooting:** See new `/aws_deployment_guide.md`, and extensive notes in `CHANGELOG.md` for real-world issues encountered and solved.

### Changed

- **Default LLM and embedding model IDs:** Updated defaults in `.env.example` for Anthropic Claude 3.5 and Cohere v4:0, matching latest supported Bedrock endpoints and embedding dimension (1536).
- **Backend/Frontend launch scripts:** Each startup script now prints clear, colorized cloud-local diagnostic headers and URLs that reflect AWS env variables, improving dev/prod consistency.
- **Port configuration:** All services (backend via Uvicorn, frontend via Gradio) now allow for proper port override using standard AWS/App Runner conventions. Gradio no longer hardcodes the port; respects `GRADIO_PORT` and App Runner env.
- **.gitignore** updated: binary doc types (`*.pdf`) now excluded by default.

### Fixed

- **Upload directory errors on Lambda:** Protects against OSError/"read-only filesystem" by using runtime temp folder.
- **Dev/prod env variable confusion:** All config vars now load in correct order for both scripts and application entrypoints.
- **Multiple deployment pain points:** Changelog and `/aws_deployment_guide.md` list and solve key obstacles, especially with App Runner health checks, port/env mismatch, and Docker image platform/manifest types for Lambda/ECR.

### Migration Notes

- To deploy backend on Lambda with ECR, ensure Docker images are built for `linux/amd64` and `application/vnd.docker.distribution.manifest.v2+json` format.
- To deploy frontend on App Runner, ensure Docker images listen on the port provided by the `PORT` env variable, or configure App Runner's image settings to use `GRADIO_PORT`.
- Check `/aws_deployment_guide.md` and long-form CHANGELOG section for detailed troubleshooting and verified AWS configuration examples.

### See Also

- [aws_deployment_guide.md](./aws_deployment_guide.md): Detailed end-to-end instructions for AWS Lambda + API Gateway (backend) and App Runner (frontend).
- [local_development.md](./local_development.md): Local testing & dev environment setup, now matching production env structure.
- [architecture.md](./architecture.md): System design, cloud-native patterns, and user/session flow.
- See CHANGELOG below for real-world fixes, migration steps, and troubleshooting cheatsheet, updated for 2025 cloud deployment.

## [0.6.0] 2025-12-01 - Frontend Refactor, Session Management, AWS Secrets

### Added

- **Embedding dimension migration**: Database `document_chunks.embedding` column was migrated from dimension 1024 to 1536 to support improved embedding models. See Alembic migration `9ff57d084d8a_change_embedding_dimension_from_1024_to_.py`. _(All existing chunk vectors must be re-embedded to avoid incompatible shape errors.)_
- **Support for more document types in uploads**: Backend and frontend now allow PDF, DOCX, and TXT document upload. Dependencies `pypdf` and `python-docx` added to project.
- **New local-only testing scripts**:
  - `scripts/test_basic_processing.py`: Tests document text extraction, chunking, and DB integration without AWS (fast local dry-run).
  - Enhanced `scripts/test_api.py` to allow custom backend URL via `$BACKEND_API_URL`.
- **Backend/Frontend dev scripts now auto-load environment variables**: All `scripts/start_*.sh` scripts will load config from `.env`, improving DX and reducing config drift between dev/prod.
- **Frontend hot-reload dev script**: Run `./scripts/start_frontend_dev.sh` for Gradio instant-reload in local dev.
- **Updated `.env.example`** with correct embedding dims, model IDs, and all optional config variables documented for both backend and frontend.

### Changed

- **Embedding model ID and dimension updated** in `.env.example` for newest (Cohere v4:0 and Anthropic Claude 3.5) models and default dimensions.
- **Frontend status update refactor**: All Gradio UI status returns now use a single consistent `gr.update(value=..., visible=True)` pattern. Cleans up all validation and success/error prompts for login, registration, and logout for fuller accessibility and maintainability.
- **Chatbot history now uses Gradio's "messages" format** rather than Python tuples, for native multi-turn thread rendering and streaming support. All history and message construction logic updated for this format in both code and frontend.
- **Frontend/server startup scripts improved**: All local scripts now display detailed status, port info, and helpful reminders for running backend/frontend together, with clear prompts and colorized warnings.
- **Gradio version in requirements bumped, dependencies for `pypdf` and `python-docx` added**.

### Fixed

- **.gitignore improved** to exclude all `.pdf` files from repo.
- **Environment loading order fixed** in all scripts (`.env` always sourced before activating venv or running app).
- **Backend health/test scripts now robust to environment overrides**.

### Migration Notes

- Alembic migration required: `alembic upgrade head` to migrate `document_chunks.embedding` to 1536 dimensions.
- Re-embed all existing chunk vectors or clear your DB for new embeddings if upgrading from 0.5.0 or earlier.

### Developer Info

- All configs are now available and documented in `.env.example`.
- Hot-reload your Gradio frontend with `./scripts/start_frontend_dev.sh`
- All AWS profile/region/env config for scripting is centralized—run backend/frontend concurrently with proper environment.
- Code, linted/autoformatted with `ruff`.

## [0.5.0] - 2025-11-30 - Frontend Refactor, Session Management, AWS Secrets

#### Added

- **Frontend structure refactored**: Reorganized Gradio components into logical modules (`register_tab`, `login_tab`, `chat_tab`, and `document_tab`) for easier maintenance.
- **Session management introduced**: Added backend-integrated session capability to support authenticated user flows and persistent conversation context.
- **Dedicated registration and login tabs**: UI components for registration/login now have their own modules with enhanced validation (e.g., password strength, confirm password, required fields).
- **Enhanced API client** for streamlined backend communication: uniform request/response handling for user registration, login, and document management.
- **AWS Secrets Manager integration**: App configuration (e.g., sensitive credentials, endpoints) now retrieved securely via AWS Secrets Manager; see `src/core/secrets.py`.
- **Improved configuration management**: All secret/config access is centralized; environment and secrets are loaded at startup.
- **Updated documentation**: Details on new frontend structure and AWS Secrets usage.

#### Changed

- **Refactored frontend logic** for improved testability, separation of concerns, and more robust UI feedback.
- **API error messages** and status prompts unified and translated to clear, user-friendly Chinese.
- **Enhanced Docker setup**: Environment variable management cleaned up for dev/prod, with specific notes on how lambdas/frontend communicate.

#### Fixed

- **Login/registration race conditions**: Sessions now properly isolated; UI responses for success/error made clearer.
- **Various UI bugs**: Ensured all frontend tabs are reactive to session state and provide context-aware controls.

#### Notes

- Developer tip: See new top-level directory structure and module organization under `src/frontend/tabs`.
- Security: All sensitive config and credentials (not stored in code) should be injected via AWS Secrets or environment.
- All code passes `ruff check` and is formatted with `ruff format`.

## [0.4.2] - 2025-11-29 - Multi-file Upload Support

#### Added

- Multi-file upload support in the backend and Gradio frontend:
  - Backend `/upload/document` endpoint now accepts multiple files simultaneously, validating and processing each file independently.
  - Introduced new `DocumentUploadResult` schema to represent status and details for each uploaded file.
  - Upload response schema updated to include overall summary and per-file results (success/failed counts, error messages).
  - Frontend upload component updated to allow selecting multiple files (`file_count="multiple"`) with an improved label.
  - Enhanced frontend upload logic to:
    - Accept a list of files and manage them safely with `ExitStack`.
    - Display a summary of successes/failures and list failed files with error messages after upload.
    - Update the document list table in real time to reflect the state of each file (pending, succeeded, failed).

#### Changed

- Simplified multi-file task management with FastAPI's native `BackgroundTasks`, leveraging FIFO task execution without introducing a queue system.
- Improved feedback to users:
  - Upload dialog now clearly distinguishes how many files were successfully processed and lists those that failed.
  - All error messages are now clearer and presented in Chinese for end-user guidance.
  - Real-time feedback in the UI table for ongoing status of uploaded files.
- Updated technical documentation with new instructions for batch/multi-file upload, including both user and developer perspectives.

#### Fixed

- Ensured that an error processing one file does not interrupt or affect the upload of other files; tasks complete independently.
- File resource management on frontend now uses `ExitStack` to correctly handle context managers for multiple files, preventing resource leaks.
- All code changes have passed `ruff check` and have been formatted with `ruff format`.

#### Notes

- This update prioritizes a streamlined user experience for batch uploading, robust per-file error handling, and improved observability in both backend and frontend flows.

## [0.4.1] - 2025-11-28 - PDF parsing improvements

#### Changed

- Improved PDF extraction: PDF parsing logic now skips pages with broken/garbled encoding by calculating the Chinese character ratio per page. Only pages with >30% Chinese characters are included as valid parsed content. This improves text extraction robustness, especially for primarily Chinese documents with occasional non-unicode English/garbled pages.
- PDF extraction logging is more granular: now logs number of pages processed, pages skipped, and reports character counts after extraction.
- Document chunking logic made context-aware and semantic:
  - Structured documents (e.g., laws, regulations) with article/section markers are now chunked by detected articles/sections, using patterns for "第X條" and English "Article X"/"Section X" (requires at least 3 markers to be considered structured).
  - Unstructured documents are chunked by paragraph, maintaining paragraph boundaries.
  - Large semantic units are further split by sentence boundaries with overlap for context preservation.
  - Chunk size and overlap defaults changed to 512 characters (from 1000) and 128 characters (from 200), respectively.
  - Minimum chunk size enforced at 300 chars; chunks are constructed to preserve as much semantic information as possible, adding context overlap between them.
  - Added debug-level logging to chunking process for improved observability.

#### Fixed

- Fixed an extraction bug where empty or whitespace-only extracted text could cause errors downstream by validating content and erroring more gracefully.
- PDF and DOCX text extraction now removes excess whitespace, ensures proper newline handling, and is more robust to file encoding issues.

## [0.4.0] - 2025-11-28 - File Uploads, Parsing, and Document Support

#### Added

- **File Upload and Document Parsing Support**
  - Added robust document upload functionality (PDF, TXT, DOCX, DOC) with file type validation.
  - Integrated document parsing pipeline using:
    - `python-docx` for DOCX support.
    - `pypdf` for PDF extraction.
  - Uploaded files stored to configurable directory (`UPLOAD_DIR`), supported file types and upload limits are now configurable in `.env.example`.
  - Added backend routes and logic for file upload, parse, and indexing; Error handling added for unsupported/invalid files.
  - Environment variables in `.env.example` for upload and parsing configuration, with clearly marked defaults and options.

- **Frontend Integration**
  - Improved Gradio frontend to support uploading documents for embedding/RAG use.
  - Extended user instructions and placeholders related to document uploads.

- **Packaging**
  - Added new dependencies:
    - `python-docx`
    - `pypdf`
    - Documented these in requirements/lock files.

#### Changed

- Updated API and backend structure to support multi-format document ingestion and indexing.
- Improved logging and validation in file handling flows.
- Enhanced changelog and README documentation to cover file upload features and setup.
- Updated `.env.example` configuration with new sections for File Upload and Frontend settings.

#### Fixed

- Addressed minor bugs in previous file handling sample code.
- Improved input validation and error messages for upload endpoints.

#### Deprecated

- No deprecations in this release.

## [0.3.0] - 2025-11-26 - AWS Bedrock Integration

#### Added

- **AWS Bedrock Integration**
  - Added `src/core/bedrock_client.py`: Modular Amazon Bedrock client to interact with Claude Sonnet 4 LLM.
  - Integrated Bedrock LLM invocation in chat service.
  - Added support for configuration-based LLM hyperparameters (`LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_TOKENS`) and global model parameters.
  - New environment variable support: `AWS_REGION`, `AWS_PROFILE`, LLM and embedding model IDs.
  - Added `.env.example` documentation and hard requirements for `AWS_REGION`, `AWS_PROFILE` config.

- **System Prompts & HR RAG Mode**
  - Added system prompt templates for HR advisor chatbot, supporting both standard and RAG-enabled modes (`src/prompts/system_prompts.py`).
  - Support for Traditional Chinese response format and HR-specific conversational limitations.
  - Centralized prompt logic with `get_system_prompt()`.

- **Chat Backend Enhancements**
  - Fully replaced echo logic with real LLM responses in `src/services/chat_service.py`.
  - Conversation history formatting for multi-turn chat and system prompt injection.
  - Error handling and logging integrated with backend generation logic.

- **Configuration Improvements**
  - Centralized all LLM and RAG parameters in `src/core/config.py` (`Settings`), including: max conversation history, chunk size/overlap, search ratio, RAG toggle (`ENABLE_RAG`).
  - Updated `.env.example` and documentation for new config variables.

- **Scripts & Developer Experience**
  - Added `scripts/start_backend_with_aws.sh` to simplify starting backend with AWS Vault credentials.
  - Improved guidance and documentation for AWS Vault workflow.

- **Documentation**
  - Updated README: clarified project phases, AWS configuration steps, and marked completed tasks in phase 1 and phase 4.
  - Expanded setup and deployment docs with Aurora, LLM config, and local/test mode differences.

#### Changed

- Updated Chat Service to support Bedrock Claude Sonnet 4 responses with conversation history and system prompt.
- Restructured prompt handling to support both HR advisor standard and RAG document-augmented flows (RAG toggling supported but not enabled by default).
- Improved error handling/logging around LLM failures and user messaging.

#### Fixed

- Status: No major bug fixes in this version.

#### Deprecated

- Echo-based chat responses have been removed in favor of direct Claude Sonnet 4 integration.

### Added

#### Authentication & Security

- User registration system with email validation
  - `POST /auth/register` - New user registration endpoint
  - Full name field support (optional)
  - Password confirmation validation (minimum 6 characters)
- JWT token-based authentication with access tokens
- Password hashing utilities using bcrypt (`src/core/security/password.py`)
- Authorization headers with Bearer token support
- Secure user session management in frontend

#### Document Processing & Management

- Document processor service (`src/services/document_service.py`)
  - Chunking strategy with configurable size and overlap
  - Text extraction from PDF, DOCX, and TXT files
  - Background processing simulation (AWS Lambda simulation)
  - Document status tracking (pending, processing, completed, failed)
  - Error handling and logging
- Document management endpoints:
  - `GET /upload/documents` - List user's uploaded documents
  - `DELETE /upload/documents/{id}` - Delete document and all chunks
- Background task processing for async document handling
- File storage system with unique filename generation
- Document metadata tracking (file size, type, chunk count, upload date)

#### Database & Models

- New database migration: `34c68b28c841_add_user_id_status_and_error_message_to_`
  - Added `user_id` foreign key to documents table (CASCADE on delete)
  - Added `status` field (varchar 20) for processing status
  - Added `error_message` field (text, nullable) for error tracking
- Document model enhancements with new fields
- Database session improvements for background tasks

#### Frontend (Gradio)

- Complete UI redesign with tabbed interface:
  - Registration tab (index 0) - New user registration form
  - Login tab (index 1) - User authentication
  - Chat tab (index 2) - Multi-turn conversations
  - Document Management tab (index 3) - File upload and management
- Bot avatar image (`assets/bot_avatar.png`)
- Document list display with DataFrames:
  - Shows document ID, filename, type, size, status, chunk count, upload date
  - Real-time status updates (pending, processing, completed, failed)
- Document deletion functionality with confirmation
- Enhanced chat interface:
  - User/bot avatars
  - Improved message formatting
  - Better error handling
  - Real-time conversation loading
- Session state management:
  - User info (user_id, username, email, access_token)
  - Current conversation tracking
- Interactive button states based on authentication
- Loading indicators for async operations
- Logout functionality
- Refresh buttons for conversations and documents
- Chinese language UI (Traditional Chinese)

#### Documentation

- Database migrations guide in `CLAUDE.md`
  - Alembic command reference
  - Best practices for migrations
  - Important notes on using `uv run` prefix
  - Migration workflow guidelines

### Changed

#### API Routes

- **Upload route** (`src/api/routes/upload.py`) - Complete rewrite:
  - From simple file acceptance to full document processing
  - Added background task integration
  - Enhanced error handling and validation
  - File type validation (pdf, txt, docx)
  - Document record creation in database
  - Status messages with detailed feedback
- **Chat route** (`src/api/routes/chat.py`) - Performance optimization:
  - Fixed conversation list query to include message count efficiently
  - Optimized database query to avoid N+1 problem
  - Returns message count directly from query

#### Frontend

- Gradio interface completely redesigned:
  - From simple login/chat to full-featured application
  - Multi-tab navigation system
  - Enhanced user experience with better feedback
  - Improved error messages and status displays
  - Better visual hierarchy and layout
- Authentication flow improved:
  - Registration and login in separate tabs
  - Token-based API calls
  - Automatic tab switching after successful auth
  - Button state management based on auth status

#### Configuration

- Database session management updated for background task support
- API dependency injection for better session handling

### Fixed

- Conversation list performance issue (N+1 query problem)
  - Now returns message count directly from optimized query
  - Significantly faster for users with many conversations
- Document model SQLAlchemy compatibility
- Background task database session handling

### Technical Details

- **Document Processing**:
  - Chunk size: 512 characters (configurable)
  - Chunk overlap: 50 characters (configurable)
  - Supported file types: PDF, DOCX, TXT
  - Max file size: Not enforced (TBD)
  - Processing: Background tasks (simulates AWS Lambda)
- **Storage**:
  - Local: `uploads/` directory
  - Filename format: `{uuid}_{original_filename}`
- **Authentication**:
  - JWT tokens with Bearer scheme
  - Password hashing: bcrypt with automatic salt
  - Token stored in frontend session
- **Database**:
  - New migration applied: document fields extended
  - Foreign key constraints with CASCADE delete
  - Status tracking for document processing pipeline
- **UI Language**: Traditional Chinese (繁體中文)

### Migration Notes

To apply this version's database changes:

```bash
# Apply new migration
uv run alembic upgrade head

# Verify current revision
uv run alembic current
```

### Breaking Changes

- Document upload API now requires authentication token (not just user ID header)
- Document model structure changed (requires migration)
- Frontend session state structure changed

### Known Limitations

- Document processing is simulated (no actual chunking/embedding yet)
- File uploads stored locally (S3 integration pending)
- No file size limits enforced
- Background processing is synchronous simulation (true async pending)
- LLM and embedding integration not yet implemented

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
