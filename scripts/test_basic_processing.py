"""
Basic test script for document processing (without AWS Bedrock).

Tests only the local components:
1. Text extraction from TXT/PDF/DOCX
2. Text chunking with overlap
3. Database operations
"""

import logging
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models import User
from src.models.document import Document
from src.services.document_service import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_document() -> str:
    """Create a temporary test document."""
    content = """
    Employee Leave Policy

    1. Annual Leave
    All full-time employees are entitled to 15 days of annual leave per year.
    Leave must be requested at least 2 weeks in advance for approval.

    2. Sick Leave
    Employees receive 10 days of paid sick leave annually.
    A medical certificate is required for absences exceeding 2 consecutive days.

    3. Remote Work Policy
    Employees may work remotely up to 2 days per week.
    Remote work requests must be approved by the direct manager.
    """

    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    temp_file.write(content)
    temp_file.close()

    return temp_file.name


def test_text_extraction_and_chunking():
    """Test text extraction and chunking without Bedrock."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Text Extraction and Chunking (Local Only)")
    logger.info("=" * 60)

    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get or create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="dummy_hash",
                full_name="Test User",
                is_active=True,
                is_superuser=False,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        logger.info(f"✓ Using test user: {test_user.id}")

        # Create test document
        test_file = create_test_document()
        logger.info(f"✓ Created test file: {test_file}")

        # Create processor
        processor = DocumentProcessor(db)

        # Test text extraction
        logger.info("\n1. Testing text extraction...")
        text = processor.extract_text(test_file, "txt")
        logger.info(f"✓ Extracted {len(text)} characters")
        logger.info(f"   Preview: {text[:100]}...")

        # Test chunking
        logger.info("\n2. Testing text chunking...")
        chunks = processor.chunk_text(text)
        logger.info(f"✓ Created {len(chunks)} chunks")
        for idx, chunk in enumerate(chunks[:3], 1):
            logger.info(f"   Chunk {idx}: {len(chunk)} chars - {chunk[:50]}...")

        # Test BM25 indexing
        logger.info("\n3. Testing BM25 index creation...")
        bm25_vectors = processor.create_bm25_indexes(chunks)
        logger.info(f"✓ Created {len(bm25_vectors)} BM25 vectors")

        logger.info("\n✅ All basic processing tests PASSED!")
        logger.info("\n📝 Note: To test full RAG functionality with embeddings,")
        logger.info("   you need to configure AWS Bedrock credentials:")
        logger.info("   1. Run: aws-vault add ting-bedrock")
        logger.info("   2. Enter your AWS credentials")
        logger.info("   3. Run: aws-vault exec ting-bedrock -- python scripts/test_rag.py")

    except Exception as e:
        logger.error(f"✗ Test FAILED: {e}")
        import traceback

        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    test_text_extraction_and_chunking()
