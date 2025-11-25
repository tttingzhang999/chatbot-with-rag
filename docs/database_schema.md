# Database Schema Documentation

## Overview

The HR Chatbot RAG system uses PostgreSQL with pgvector extension to store documents, vector embeddings, and conversation history. The schema is designed to support:

- **Hybrid Search**: Combining semantic search (vector embeddings) and BM25 (full-text search)
- **Multi-turn Conversations**: Maintaining conversation history and context
- **Document Management**: Tracking original documents and their processed chunks

## Technologies

- **PostgreSQL**: Main relational database
- **pgvector**: Vector similarity search extension
- **pg_trgm**: Trigram-based text search for better BM25 performance
- **SQLAlchemy**: ORM for Python
- **Alembic**: Database migration management

## Tables

### 1. documents

Stores metadata about uploaded documents.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| file_name | VARCHAR(255) | Original filename |
| file_path | VARCHAR(512) | S3 path to the document |
| file_type | VARCHAR(50) | File type (pdf, docx, txt, etc.) |
| file_size | INTEGER | File size in bytes |
| upload_date | TIMESTAMP | When the document was uploaded |
| metadata | JSONB | Additional flexible metadata |

**Relationships**:
- One-to-many with `document_chunks`

### 2. document_chunks

Stores processed document chunks with embeddings and full-text search data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| document_id | UUID | Foreign key to documents table |
| chunk_index | INTEGER | Order of chunk within the document |
| content | TEXT | Actual text content of the chunk |
| embedding | VECTOR(1024) | Vector embedding (Cohere Embed v4) |
| content_tsvector | TSVECTOR | Full-text search vector for BM25 |
| chunk_metadata | JSONB | Chunk-specific metadata (position, page, etc.) |
| created_at | TIMESTAMP | When the chunk was created |

**Indexes**:
- `idx_embedding_vector`: IVFFlat index for vector similarity search (cosine distance)
- `idx_content_tsvector`: GIN index for full-text search
- `idx_document_chunk`: Composite index on (document_id, chunk_index)

**Relationships**:
- Many-to-one with `documents`

### 3. conversations

Stores conversation sessions for multi-turn chat.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | Optional user identifier |
| title | VARCHAR(255) | Optional conversation title |
| created_at | TIMESTAMP | When the conversation started |
| updated_at | TIMESTAMP | Last update time |
| metadata | JSONB | Additional flexible metadata |

**Indexes**:
- `idx_conversation_user_id`: Index on user_id
- `idx_conversation_created_at`: Index on created_at

**Relationships**:
- One-to-many with `messages`

### 4. messages

Stores individual messages within conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| conversation_id | UUID | Foreign key to conversations table |
| role | VARCHAR(20) | Message role (user, assistant, system) |
| content | TEXT | Message content |
| retrieved_chunks | JSONB | List of chunk IDs used for this response |
| retrieval_metadata | JSONB | Retrieval scores and metadata |
| created_at | TIMESTAMP | Message timestamp |

**Indexes**:
- `idx_message_conversation_id`: Index on conversation_id
- `idx_message_created_at`: Index on created_at
- `idx_message_role`: Index on role

**Relationships**:
- Many-to-one with `conversations`

## Hybrid Search Implementation

### Semantic Search

Uses pgvector's cosine distance for vector similarity:

```sql
SELECT id, content, 1 - (embedding <=> query_embedding) AS similarity
FROM document_chunks
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

### BM25 Search

Uses PostgreSQL's full-text search with ranking:

```sql
SELECT id, content, ts_rank(content_tsvector, query) AS rank
FROM document_chunks
WHERE content_tsvector @@ query
ORDER BY rank DESC
LIMIT 5;
```

### Hybrid Combination

Retrieve top K results from both methods and combine them based on a configurable ratio (default 50/50).

## Vector Embedding Details

- **Model**: Cohere Embed v4 (via Amazon Bedrock)
- **Dimensions**: 1024
- **Distance Metric**: Cosine distance
- **Index Type**: IVFFlat (suitable for datasets up to 1M vectors)

For larger datasets (>1M vectors), consider using HNSW index instead:

```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## Database Initialization

### Using init_db.py

Direct initialization without migrations:

```bash
python -m src.db.init_db
```

This will:
1. Create the `vector` and `pg_trgm` extensions
2. Create all tables as defined in the models

### Using Alembic (Recommended)

For production-ready migration management:

```bash
# Initialize Alembic (only needed once)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## Configuration

Required environment variables in `.env`:

```bash
# Database connection (constructed from Secrets Manager or direct)
DATABASE_URL=postgresql://user:password@host:port/database

# Or use Secrets Manager
DB_SECRET_NAME=hr-chatbot/db-credentials
AWS_REGION=us-east-1

# RAG Configuration
EMBEDDING_DIMENSION=1024
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_CHUNKS=10
SEMANTIC_SEARCH_RATIO=0.5
```

## Performance Considerations

### Vector Search Optimization

- **IVFFlat lists parameter**: Set to ~sqrt(total_rows) for optimal performance
- **Chunk size**: Balance between context and search granularity (default: 1000 chars)
- **Batch insertions**: Use bulk insert for better performance when processing multiple documents

### Full-Text Search Optimization

- Keep `content_tsvector` updated with triggers or application logic
- Use appropriate text search configuration (e.g., 'english' for English documents)
- Consider `ts_rank_cd()` for position-weighted ranking

### Index Maintenance

```sql
-- Reindex vector index if data distribution changes significantly
REINDEX INDEX idx_embedding_vector;

-- Update full-text search statistics
ANALYZE document_chunks;
```

## Example Queries

### Insert Document Chunk

```python
from src.models import Document, DocumentChunk
from src.db import SessionLocal

db = SessionLocal()

# Create document
doc = Document(
    file_name="employee_handbook.pdf",
    file_path="s3://bucket/documents/handbook.pdf",
    file_type="pdf",
    file_size=1024000,
)
db.add(doc)
db.commit()

# Create chunk with embedding
chunk = DocumentChunk(
    document_id=doc.id,
    chunk_index=0,
    content="Employee benefits include...",
    embedding=[0.1, 0.2, ...],  # 1024-dimensional vector
    chunk_metadata={"page": 1, "start_char": 0, "end_char": 1000},
)
db.add(chunk)
db.commit()
```

### Hybrid Search Query

```python
from sqlalchemy import func, text
from src.models import DocumentChunk

# Semantic search (top 5)
semantic_results = db.query(DocumentChunk).order_by(
    DocumentChunk.embedding.cosine_distance(query_embedding)
).limit(5).all()

# BM25 search (top 5)
bm25_results = db.query(DocumentChunk).filter(
    DocumentChunk.content_tsvector.match(query_text)
).order_by(
    func.ts_rank(DocumentChunk.content_tsvector, func.to_tsquery(query_text)).desc()
).limit(5).all()

# Combine results
all_chunk_ids = list(set([c.id for c in semantic_results + bm25_results]))
```

## Migration Strategy

1. **Development**: Use `init_db.py` for quick setup
2. **Staging/Production**: Use Alembic migrations for version control and rollback capability
3. **Schema Changes**: Always create a new Alembic revision for any model changes

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add user_id index to conversations"

# Review the generated migration file
# Edit if necessary (Alembic may not detect all changes)

# Apply migration
alembic upgrade head
```

## Future Enhancements

- **Partitioning**: Consider table partitioning for `document_chunks` if dataset grows very large
- **Read Replicas**: Use Aurora read replicas for scaling read operations
- **Caching**: Implement Redis cache for frequently accessed chunks
- **Compression**: Enable PostgreSQL TOAST compression for large text fields
