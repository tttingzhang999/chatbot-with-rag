# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an HR Chatbot with RAG (Retrieval-Augmented Generation) capabilities, deployed on AWS infrastructure. The system uses hybrid search (Semantic + BM25) to retrieve relevant documents and Claude Sonnet 4 for multi-turn conversations.

**Project Timeline**: Nov 2025 - End of Dec 2025

## System Architecture

### Core Components

The system consists of two main Lambda functions deployed as container images:

1. **Document Processor Lambda** (`src/document_processor/`)
   - Triggered by S3 upload events
   - Performs chunking, embedding generation (Cohere Embed v4), and BM25 index creation
   - Stores processed data in Aurora PostgreSQL with pgvector extension

2. **Chatbot Backend Lambda** (`src/chatbot/`)
   - Handles API Gateway requests (`/chat`, `/query`)
   - Executes hybrid search (Semantic + BM25)
   - Generates responses using Claude Sonnet 4 with conversation history

### Data Flow

**Document Processing**:

```
S3 Upload → Lambda Trigger → Chunking → Cohere Embed v4 → Aurora PostgreSQL (vectors + BM25 index)
```

**Query Processing**:

```
User Question → Question Embedding → Hybrid Search (Aurora) → Context Retrieval → Claude Sonnet 4 → Answer
```

### AWS Service Stack

- **Compute**: Lambda (container images from ECR)
- **Storage**: S3 (raw documents), Aurora PostgreSQL Serverless (vectors + metadata)
- **AI/ML**: Amazon Bedrock (Claude Sonnet 4, Cohere Embed v4)
- **Network**: API Gateway, Route 53 (\*.going.cloud), Certificate Manager
- **Security**: Secrets Manager (DB credentials), IAM
- **Frontend**: Gradio interface

## Development Commands

### Environment Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Setup AWS Vault for local development
aws-vault add <profile-name>
aws-vault exec <profile-name> -- aws s3 ls
```

## Local Development Modes

The project supports two development modes:

### Mode 1: Native Development (Recommended for Active Development)

For fast development with hot-reload:

```bash
# Prerequisites: PostgreSQL installed and running locally, aws-vault configured

# 1. Initialize database (first time only)
./scripts/local/init-db.sh

# 2. Start backend with aws-vault (Terminal 1)
./scripts/local/start-backend.sh <aws-profile>

# 3. Start frontend (Terminal 2)
./scripts/local/start-frontend.sh

# Access:
# - Frontend: http://localhost:5173 (Vite dev server with HMR)
# - Backend: http://localhost:8000 (FastAPI with --reload)
# - API Docs: http://localhost:8000/docs
```

**Features:**

- ✅ Hot-reload for both frontend and backend
- ✅ Fast startup time
- ✅ Instant feedback on code changes
- ✅ Uses local PostgreSQL database
- ✅ Secure AWS credentials via aws-vault

**Environment Setup:**

- Backend: `.env` (root) + aws-vault for AWS credentials
- Frontend: `apps/frontend/.env.local`

**aws-vault Setup:**

```bash
# Install aws-vault
brew install aws-vault  # macOS

# Configure profile
aws-vault add <profile-name>
# Enter AWS Access Key ID and Secret Access Key when prompted

# Verify setup
aws-vault exec <profile-name> -- aws sts get-caller-identity
```

### Mode 2: Docker Compose (Production-Ready Testing)

For testing production behavior locally:

```bash
# 1. Configure environment (first time only)
cp .env.example .env

# 2. Start all services with aws-vault (database + backend + frontend)
aws-vault exec <profile-name> -- docker-compose up --build

# Access:
# - Frontend: http://localhost:5173 (Nginx static files)
# - Backend: http://localhost:8000 (Uvicorn production mode)
# - API Docs: http://localhost:8000/docs

# 3. Stop services
docker-compose down
```

**Features:**

- ✅ Simulates production environment
- ✅ No hot-reload (like production)
- ✅ Frontend served as static files via Nginx
- ✅ Backend runs without --reload flag
- ✅ Uses Docker PostgreSQL container
- ✅ AWS credentials securely injected via aws-vault
- ✅ Uses local file storage (no S3 presigned URLs needed)

**File Storage:**

- Files are stored locally in `./uploads` directory (mounted to container)
- No CORS configuration needed for S3
- Production deployment will use S3 with presigned URLs

**IMPORTANT**: Code changes require rebuild (`aws-vault exec <profile> -- docker-compose up --build`)

See [`docs/local_development.md`](./docs/local_development.md) for detailed local development guide.

### Production Testing (With AWS)

```bash
# Test document processor
python -m src.document_processor

# Test retrieval system
python -m src.retrieval
```

### Database Migrations

```bash
# Create a new migration (auto-generate from model changes)
uv run alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
uv run alembic upgrade head

# Downgrade to a specific revision
uv run alembic downgrade <revision_id>

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history

# Downgrade one revision
uv run alembic downgrade -1
```

**Important Notes:**

- Always use `uv run` prefix when running alembic commands
- Review auto-generated migrations before applying them
- Test migrations on local database before production
- Create meaningful migration messages using conventional commit format

### Code Quality

```bash
# Run linting with ruff
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Run pre-commit on all files
pre-commit run --all-files
```

### Deployment to AWS

The project includes automated deployment scripts for backend and frontend:

**Deploy Backend (Lambda):**

```bash
./scripts/deploy/deploy-backend.sh
```

**Deploy Frontend (S3/CloudFront):**

```bash
./scripts/deploy/deploy-frontend.sh
```

**Deployment Details:**

- **Backend**: Builds Docker image, pushes to ECR, updates Lambda function
- **Frontend**: Builds React app, uploads to S3, invalidates CloudFront cache
- **Prerequisites**: AWS CLI, configured AWS profile (use aws-vault)

**Note**: Lambda environment variables are managed by Terraform. Run `cd infrastructure/terraform && terraform apply` to update configuration.

## Technical Considerations

### RAG Implementation

**Hybrid Search Strategy**:

- Combines Semantic Search (pgvector cosine similarity) with BM25 (keyword-based TFIDF)
- Default ratio: 50/50, but configurable as hyperparameter
- Example: Retrieve top 10 chunks (5 from semantic, 5 from BM25)

**Hyperparameters to Tune**:

- Chunk size and overlap size
- Number of retrieved chunks (top K)
- Semantic vs BM25 ratio
- Use validation set for tuning, test set for final evaluation

**Multi-turn Conversation**:

- Maintain conversation history in context
- Design system prompts carefully
- Implement context window management to avoid token limits
- Consider conversation summarization for long dialogues

### Database Schema

Aurora PostgreSQL with pgvector extension:

- Stores text chunks with metadata
- Vector embeddings (from Cohere Embed v4)
- BM25 index data (TFIDF-based)
- All accessed via Secrets Manager credentials

### AWS Cost Awareness

- Test locally first before deploying to AWS
- Use serverless services (Lambda, Aurora Serverless) for cost efficiency
- Monitor Bedrock API usage (Claude Sonnet 4, Cohere Embed v4)
- **Critical**: Do not modify existing Route 53 resources

## Git Workflow

### Commit Convention

Follow Conventional Commits format:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code refactoring
- `test:` - Test-related changes
- `chore:` - Misc changes (dependencies, etc.)

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Commit changes
git add .
git commit -m "feat: add document chunking strategy"

# Push and create merge request
git push origin feature/your-feature-name
```

## Environment Variables

Required `.env` configuration (never commit to git):

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=<your-profile>

# Database
DB_SECRET_NAME=<secret-manager-name>

# S3
DOCUMENT_BUCKET=<s3-bucket-name>

# Bedrock Models
LLM_MODEL_ID=anthropic.claude-sonnet-4
EMBEDDING_MODEL_ID=cohere.embed-v4
```

## Architecture Documentation

For detailed architecture diagrams including RAG flow, AWS services integration, and sequence diagrams, refer to `architecture.md`. The diagrams use Mermaid format and show:

- RAG core processing flow (document processing + query/chat)
- Complete AWS service architecture
- Detailed data flow sequence diagrams

## RAG Framework Selection

The project may use either LangChain or LlamaIndex for RAG implementation. When implementing RAG components, ensure consistency with the chosen framework throughout the codebase.

## Development Principles

- **Always test locally first**: Run components locally before AWS deployment
- **Incremental development**: Build and test each pipeline component separately
- **AWS vs GCP awareness**: This project uses AWS; refer to the service mapping table in README.md when comparing with GCP
- **Quality standards**: All code must pass ruff linting and pre-commit hooks before commit
- **Ask for help**: Consult supervisor, mentor, or colleagues when needed
- **Use AI tools**: Feel free to use AI development tools for assistance

## Reference Resources

- Project Google Drive: https://drive.google.com/drive/u/1/folders/1KHnvLLubLUTg5nwfR3dZKgfWanQXw7UQ
- LangChain Documentation: https://python.langchain.com/
- LlamaIndex Documentation: https://docs.llamaindex.ai/
- Amazon Bedrock Developer Guide: https://docs.aws.amazon.com/bedrock/
- pgvector GitHub: https://github.com/pgvector/pgvector

## Key Technical Terms

- **BM25**: Best Matching 25, a ranking function for information retrieval
- **TFIDF**: Term Frequency-Inverse Document Frequency
- **pgvector**: PostgreSQL extension for vector similarity search
- **Cosine Similarity**: Metric for measuring vector similarity
- **Chunking**: Strategy for splitting documents into segments with configurable size and overlap
- **Hybrid Search**: Combined semantic search (embeddings) + keyword search (BM25)

---

**Project Lead**: Ting Zhang
**Mentor**: Micheal
**Last Updated**: 2025-11-25
