# Database Setup Guide

This guide walks you through setting up the PostgreSQL database with pgvector for the HR Chatbot RAG system.

## Prerequisites

- PostgreSQL 14+ installed (or AWS Aurora PostgreSQL Serverless)
- Python 3.11+ with uv package manager
- AWS credentials configured (if using Aurora)

## Step 1: Create Database

### Local PostgreSQL

```bash
# Create database
createdb hr_chatbot

# Or using psql
psql -U postgres
CREATE DATABASE hr_chatbot;
\q
```

### AWS Aurora PostgreSQL

Use AWS Console or CLI to create an Aurora PostgreSQL Serverless cluster.

## Step 2: Enable Extensions

Connect to your database and enable required extensions:

```bash
psql -U postgres -d hr_chatbot
```

```sql
-- Enable pgvector for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for better text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify extensions
\dx
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/hr_chatbot

# For AWS Aurora with Secrets Manager
DB_SECRET_NAME=hr-chatbot/db-credentials
AWS_REGION=us-east-1

# RAG Configuration
EMBEDDING_DIMENSION=1024
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_CHUNKS=10
SEMANTIC_SEARCH_RATIO=0.5

# AWS Configuration
DOCUMENT_BUCKET=your-s3-bucket-name
LLM_MODEL_ID=anthropic.claude-sonnet-4
EMBEDDING_MODEL_ID=cohere.embed-v4
```

## Step 4: Install Python Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

## Step 5: Initialize Database Schema

### Option A: Using init_db.py (Quick Setup)

For development and quick setup:

```bash
python -m src.db.init_db
```

This will:

- Enable pgvector and pg_trgm extensions
- Create all tables defined in the models

### Option B: Using Alembic (Recommended for Production)

For production with version control:

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Review the migration file in alembic/versions/
# Edit if necessary (some changes may need manual adjustment)

# Apply migration
alembic upgrade head
```

## Step 6: Verify Setup

Connect to the database and verify tables were created:

```bash
psql -U postgres -d hr_chatbot
```

```sql
-- List all tables
\dt

-- Verify documents table
\d documents

-- Verify document_chunks table with vector column
\d document_chunks

-- Check pgvector extension is working
SELECT '[1,2,3]'::vector;
```

## Step 7: Test Database Connection

Create a simple test script `test_db.py`:

```python
from src.db import SessionLocal, engine
from src.models import Document
from sqlalchemy import text

def test_connection():
    # Test basic connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"PostgreSQL version: {result.scalar()}")

        # Test pgvector
        result = conn.execute(text("SELECT '[1,2,3]'::vector"))
        print(f"Vector test: {result.scalar()}")

    # Test ORM
    db = SessionLocal()
    try:
        count = db.query(Document).count()
        print(f"Documents count: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
```

Run the test:

```bash
python test_db.py
```

## AWS Aurora Setup (Production)

### 1. Create Aurora Cluster

```bash
aws rds create-db-cluster \
  --db-cluster-identifier hr-chatbot-cluster \
  --engine aurora-postgresql \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password <password> \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=1 \
  --engine-mode provisioned
```

### 2. Store Credentials in Secrets Manager

```bash
aws secretsmanager create-secret \
  --name hr-chatbot/db-credentials \
  --secret-string '{
    "username": "admin",
    "password": "<password>",
    "host": "<cluster-endpoint>",
    "port": 5432,
    "database": "hr_chatbot"
  }'
```

### 3. Update Application to Use Secrets Manager

The application will automatically fetch database credentials from AWS Secrets Manager when `DB_SECRET_NAME` is set in the environment.

### 4. Enable pgvector on Aurora

Connect to Aurora and enable extensions:

```bash
psql -h <cluster-endpoint> -U admin -d hr_chatbot

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## Common Issues

### Issue: "extension vector does not exist"

**Solution**: Install pgvector extension on your PostgreSQL instance.

For local PostgreSQL:

```bash
# macOS with Homebrew
brew install pgvector

# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector
```

For Aurora: pgvector is available in PostgreSQL 15.3+, no installation needed.

### Issue: "permission denied to create extension"

**Solution**: You need superuser privileges to create extensions.

```sql
-- Grant superuser (if allowed)
ALTER USER your_user WITH SUPERUSER;

-- Or have a superuser create the extensions
```

### Issue: Alembic can't detect pgvector types

**Solution**: Ensure `pgvector` is imported in your models and alembic env.py.

### Issue: Connection refused from Lambda

**Solution**:

- Ensure Lambda is in the same VPC as Aurora
- Configure security groups to allow traffic
- Use Secrets Manager for credential management

## Database Maintenance

### Backup Database

```bash
# Local PostgreSQL
pg_dump -U postgres hr_chatbot > backup.sql

# Aurora (automated backups are enabled by default)
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier hr-chatbot-cluster \
  --db-cluster-snapshot-identifier hr-chatbot-snapshot-$(date +%Y%m%d)
```

### Restore Database

```bash
# Local PostgreSQL
psql -U postgres hr_chatbot < backup.sql
```

### Monitor Performance

```sql
-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## Next Steps

After setting up the database:

1. Implement document processing pipeline (`src/document_processor/`)
2. Implement retrieval system with hybrid search (`src/retrieval/`)
3. Build FastAPI endpoints for chat (`src/api/`)
4. Develop Gradio frontend (`src/frontend/`)

Refer to `docs/database_schema.md` for detailed schema documentation.
