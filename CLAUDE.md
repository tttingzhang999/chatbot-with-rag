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
- **Network**: API Gateway, Route 53 (*.goingcloud.ai), Certificate Manager
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

### Local Development (Without AWS)

For local development without AWS services:

```bash
# Initialize database
./scripts/init_db.sh

# Start FastAPI backend (Terminal 1)
./scripts/start_backend.sh
# or: python -m uvicorn src.main:app --reload --port 8000

# Start Gradio frontend (Terminal 2)
./scripts/start_frontend.sh
# or: python src/app.py

# Test API
python scripts/test_api.py
```

See [`docs/local_development.md`](./docs/local_development.md) for detailed local development guide.

### Production Testing (With AWS)

```bash
# Test document processor
python -m src.document_processor

# Test retrieval system
python -m src.retrieval
```

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

### Docker Workflow

```bash
# Build Docker image
docker build -t hr-chatbot:latest .

# Test locally
docker run -p 8080:8080 hr-chatbot:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag hr-chatbot:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-chatbot:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-chatbot:latest
```

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
