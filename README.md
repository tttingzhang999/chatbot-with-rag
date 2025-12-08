# HR Chatbot with RAG

An intelligent HR chatbot powered by Retrieval-Augmented Generation (RAG), featuring multi-turn conversations, document processing, and hybrid search capabilities. Built with FastAPI, React, and AWS infrastructure.

## Features

- **Authentication System**: JWT-based user authentication with secure registration and login
- **Multi-turn Conversations**: Context-aware dialogues powered by Claude 3.5 Sonnet via AWS Bedrock
- **Conversation Management**: Save, retrieve, and manage conversation history
- **Document Upload**: Support for PDF, DOCX, TXT, and DOC file formats
- **Document Processing**: Automated text extraction, chunking, and embedding generation
- **RAG Pipeline**: Hybrid search combining semantic search (pgvector) with keyword search (BM25)
- **Modern Frontend**: React-based UI with dark mode, chat interface, and document management
- **Production-Ready**: Deployed on AWS Lambda with containerized backend and CloudFront CDN frontend

## Tech Stack

### Backend

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **AI/ML**:
  - AWS Bedrock (Claude 3.5 Sonnet for conversations)
  - Cohere Embed v4 for document embeddings
- **RAG Framework**: LangChain
- **Document Processing**: pypdf, python-docx

### Frontend

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: TailwindCSS 4
- **State Management**: Zustand
- **Routing**: React Router v6
- **UI Components**: Radix UI primitives

### Infrastructure

- **Compute**: AWS Lambda (container images via ECR)
- **Database**: Amazon Aurora PostgreSQL Serverless
- **Storage**: Amazon S3 (documents), CloudFront (CDN)
- **API**: Amazon API Gateway
- **DNS**: Amazon Route 53
- **Secrets**: AWS Secrets Manager
- **IaC**: Terraform

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** (for local development)
- **Docker** and **Docker Compose**
- **AWS CLI** (configured with credentials)
- **[aws-vault](https://github.com/99designs/aws-vault)** - Secure AWS credential management
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager

## Installation

Choose one of the following installation methods based on your needs:

### Setup environment variables

```bash
cp .env.example .env
```

### Method 1: Local Development (Recommended for Development)

```bash
# 1. Install Python dependencies
uv sync

# 2. Initialize the database
./scripts/local/init-db.sh

# 3. Start the backend (Terminal 1)
./scripts/local/start-backend.sh <your-aws-profile-name>

# 4. Start the frontend (Terminal 2)
## go to apps/frontend directory
npm install
## return to root directory
./scripts/local/start-frontend.sh
```

**Access the application:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Method 2: Docker Compose (Production-like Testing)

```bash
# Start all services (PostgreSQL + Backend + Frontend)
aws-vault exec <your-aws-profile-name> -- docker-compose up --build
```

**Access the application:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5433 (host port)

## Environment Variables

### Required Variables

These variables **must** be set in your `.env` file:

| Variable       | Description                               | Example                                                    |
| -------------- | ----------------------------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`   | JWT token signing key                     | `a1b2c3d4e5f6...`                                          |
| `DATABASE_URL` | PostgreSQL connection string              | `postgresql://postgres:password@localhost:5432/hr_chatbot` |
| `AWS_REGION`   | AWS region for Bedrock and other services | `ap-northeast-1`                                           |

### AWS Authentication

This project uses [aws-vault](https://github.com/ByteNess/aws-vault) for secure AWS credential management. Do **NOT** store AWS credentials in the `.env` file.

### Optional Variables

All optional variables have sensible defaults. See `.env.example` for the complete list.

<details>
<summary><b>Click to expand optional variables</b></summary>

#### Application Settings

| Variable   | Description       | Default      |
| ---------- | ----------------- | ------------ |
| `APP_NAME` | Application name  | `HR Chatbot` |
| `DEBUG`    | Enable debug mode | `false`      |

#### Server Configuration

| Variable         | Description                 | Default   |
| ---------------- | --------------------------- | --------- |
| `UVICORN_HOST`   | FastAPI server host         | `0.0.0.0` |
| `UVICORN_PORT`   | FastAPI server port         | `8000`    |
| `UVICORN_RELOAD` | Auto-reload on code changes | `false`   |

#### API Settings

| Variable       | Description          | Default          |
| -------------- | -------------------- | ---------------- |
| `API_TITLE`    | API title in docs    | `HR Chatbot API` |
| `API_VERSION`  | API version          | `1.1.0`          |
| `CORS_ORIGINS` | CORS allowed origins | `*`              |

#### File Upload

| Variable               | Description               | Default            |
| ---------------------- | ------------------------- | ------------------ |
| `UPLOAD_DIR`           | Local upload directory    | `uploads`          |
| `USE_PRESIGNED_URLS`   | Use S3 presigned URLs     | `false`            |
| `SUPPORTED_FILE_TYPES` | Supported file extensions | `pdf,txt,docx,doc` |

#### Frontend

| Variable          | Description      | Default                 |
| ----------------- | ---------------- | ----------------------- |
| `BACKEND_API_URL` | Backend API URL  | `http://localhost:8000` |
| `ASSETS_DIR`      | Assets directory | `assets`                |

#### Database Query Limits

| Variable                     | Description                    | Default |
| ---------------------------- | ------------------------------ | ------- |
| `CONVERSATION_HISTORY_LIMIT` | Max conversation history items | `50`    |
| `USER_CONVERSATIONS_LIMIT`   | Max conversations per user     | `20`    |

#### Bedrock Models

| Variable                    | Description                    | Default                                     |
| --------------------------- | ------------------------------ | ------------------------------------------- |
| `CONVERSATION_LLM_MODEL_ID` | Claude model for conversations | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `TITLE_LLM_MODEL_ID`        | Model for title generation     | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `EMBEDDING_MODEL_ID`        | Cohere embedding model         | `cohere.embed-v4:0`                         |

#### LLM Parameters

| Variable                   | Description                    | Default |
| -------------------------- | ------------------------------ | ------- |
| `LLM_TEMPERATURE`          | Sampling temperature (0.0-1.0) | `0.7`   |
| `LLM_TOP_P`                | Nucleus sampling parameter     | `0.9`   |
| `LLM_MAX_TOKENS`           | Max response tokens            | `2048`  |
| `MAX_CONVERSATION_HISTORY` | Conversation rounds in context | `10`    |

#### RAG Configuration

| Variable                | Description                      | Default |
| ----------------------- | -------------------------------- | ------- |
| `ENABLE_RAG`            | Enable RAG functionality         | `false` |
| `CHUNK_SIZE`            | Document chunk size (characters) | `1000`  |
| `CHUNK_OVERLAP`         | Chunk overlap size (characters)  | `200`   |
| `TOP_K_CHUNKS`          | Number of chunks to retrieve     | `10`    |
| `SEMANTIC_SEARCH_RATIO` | Semantic vs keyword search ratio | `0.5`   |
| `RELEVANCE_THRESHOLD`   | Relevance threshold (0.0-1.0)    | `0.3`   |
| `EMBEDDING_DIMENSION`   | Embedding vector dimension       | `1536`  |

#### Production Only (AWS)

| Variable          | Description                         | Required        |
| ----------------- | ----------------------------------- | --------------- |
| `DB_SECRET_NAME`  | Secrets Manager key for database    | Production only |
| `APP_SECRET_NAME` | Secrets Manager key for app secrets | Production only |
| `DOCUMENT_BUCKET` | S3 bucket for documents             | Production only |

</details>

## Development

### Database Migrations

```bash
# Create a new migration (auto-detect model changes)
uv run alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
uv run alembic upgrade head

# Check current migration version
uv run alembic current

# View migration history
uv run alembic history

# Rollback one migration
uv run alembic downgrade -1
```

### Code Quality

```bash
# Run linting
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Run all pre-commit hooks
pre-commit run --all-files

# Run tests (if available)
pytest
```

## Deployment

Watch [Infrastructure README](infrastructure/terraform/README.md) for more details.

## Architecture

![Architecture Diagram](docs/architecture.png)

## Project Structure

```
hr-chatbot/
├── apps/
│   ├── backend/                 # FastAPI application
│   │   ├── src/
│   │   │   ├── api/            # API routes and endpoints
│   │   │   ├── core/           # Configuration and core utilities
│   │   │   ├── db/             # Database setup and session management
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   └── services/       # Business logic services
│   │   ├── alembic/            # Database migrations
│   │   ├── pyproject.toml      # Python dependencies
│   │   └── requirements.txt    # Pip requirements
│   │
│   └── frontend/               # React application
│       ├── src/
│       │   ├── components/     # React components
│       │   ├── stores/         # Zustand state stores
│       │   ├── types/          # TypeScript type definitions
│       │   └── assets/         # Static assets
│       ├── package.json        # Node dependencies
│       └── vite.config.ts      # Vite configuration
│
├── scripts/
│   ├── local/                  # Local development scripts
│   │   ├── init-db.sh         # Initialize database
│   │   ├── start-backend.sh   # Start FastAPI with hot-reload
│   │   └── start-frontend.sh  # Start Vite dev server
│   │
│   └── deploy/                 # Deployment scripts
│       ├── deploy-backend.sh  # Deploy to Lambda
│       └── deploy-frontend.sh # Deploy to S3/CloudFront
│
├── infrastructure/
│   ├── docker/                 # Dockerfiles
│   │   ├── Dockerfile.backend
│   │   └── Dockerfile.frontend
│   │
│   └── terraform/              # Infrastructure as Code
│       ├── environments/       # Environment-specific configs
│       └── modules/            # Reusable Terraform modules
│
├── docker-compose.yml          # Local multi-container setup
├── .env.example                # Environment variable template
└── README.md                   # This file
```
