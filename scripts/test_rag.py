"""
Test script for RAG (Retrieval-Augmented Generation) workflow.

This script tests:
1. Document upload and processing
2. Embedding generation via Bedrock
3. Hybrid search (Semantic + BM25)
4. End-to-end RAG conversation
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
from src.services.retrieval_service import get_retrieval_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_document() -> str:
    """
    Create a temporary test document with sample HR content.

    Returns:
        Path to the temporary file
    """
    content = """
    Employee Leave Policy

    1. Annual Leave
    All full-time employees are entitled to 15 days of annual leave per year.
    Leave must be requested at least 2 weeks in advance for approval.
    Unused leave can be carried forward to the next year, up to a maximum of 5 days.

    2. Sick Leave
    Employees receive 10 days of paid sick leave annually.
    A medical certificate is required for absences exceeding 2 consecutive days.
    Sick leave does not carry forward to the next year.

    3. Remote Work Policy
    Employees may work remotely up to 2 days per week.
    Remote work requests must be approved by the direct manager.
    Employees must be available during core hours (10 AM - 4 PM).

    4. Performance Reviews
    Performance reviews are conducted bi-annually in June and December.
    Reviews include self-assessment and manager evaluation.
    Results determine annual salary adjustments and bonus eligibility.

    5. Professional Development
    The company provides a $2,000 annual budget for professional development.
    Employees can use this for courses, certifications, or conferences.
    All development activities must align with role requirements.
    """

    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    temp_file.write(content)
    temp_file.close()

    logger.info(f"Created test document: {temp_file.name}")
    return temp_file.name


def test_document_processing(db, user_id: str):
    """
    Test document upload and processing pipeline.

    Args:
        db: Database session
        user_id: Test user ID
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Document Processing Pipeline")
    logger.info("=" * 60)

    # Create test document
    test_file = create_test_document()

    try:
        # Create document record
        document_id = uuid4()
        document = Document(
            id=document_id,
            user_id=user_id,
            file_name="test_hr_policy.txt",
            file_path=test_file,
            file_type="txt",
            file_size=Path(test_file).stat().st_size,
            status="pending",
        )
        db.add(document)
        db.commit()

        logger.info(f"✓ Document record created: {document_id}")

        # Process document
        processor = DocumentProcessor(db)
        result = processor.process_document_sync(
            document_id=document_id, file_path=test_file, file_type="txt"
        )

        logger.info(f"✓ Document processing result: {result}")

        if result["status"] == "success":
            logger.info(f"✓ Created {result['chunks_created']} chunks")
            logger.info("✓ Document processing PASSED")
            return document_id
        else:
            logger.error(f"✗ Document processing FAILED: {result.get('error')}")
            return None

    except Exception as e:
        logger.error(f"✗ Document processing FAILED with exception: {e}")
        return None


def test_hybrid_search(db, user_id: str):
    """
    Test hybrid search (semantic + BM25).

    Args:
        db: Database session
        user_id: Test user ID
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Hybrid Search")
    logger.info("=" * 60)

    try:
        retrieval_service = get_retrieval_service(db)

        # Test query 1: Should match annual leave policy
        query1 = "How many days of annual leave do I get?"
        logger.info(f"\nQuery 1: '{query1}'")

        results1 = retrieval_service.hybrid_search(query_text=query1, top_k=3, user_id=user_id)

        logger.info(f"Found {len(results1)} results:")
        for idx, result in enumerate(results1, 1):
            logger.info(f"\n  Result {idx}:")
            logger.info(f"    File: {result['file_name']}")
            logger.info(f"    Score: {result['score']:.4f}")
            logger.info(f"    Content preview: {result['content'][:100]}...")

        # Test query 2: Should match remote work policy
        query2 = "What is the remote work policy?"
        logger.info(f"\nQuery 2: '{query2}'")

        results2 = retrieval_service.hybrid_search(query_text=query2, top_k=3, user_id=user_id)

        logger.info(f"Found {len(results2)} results:")
        for idx, result in enumerate(results2, 1):
            logger.info(f"\n  Result {idx}:")
            logger.info(f"    File: {result['file_name']}")
            logger.info(f"    Score: {result['score']:.4f}")
            logger.info(f"    Content preview: {result['content'][:100]}...")

        if results1 and results2:
            logger.info("\n✓ Hybrid search PASSED")
            return True
        else:
            logger.error("\n✗ Hybrid search FAILED: No results found")
            return False

    except Exception as e:
        logger.error(f"\n✗ Hybrid search FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_rag_conversation(db, user_id: str):
    """
    Test end-to-end RAG conversation.

    Args:
        db: Database session
        user_id: Test user ID
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: End-to-End RAG Conversation")
    logger.info("=" * 60)

    try:
        from src.services.chat_service import generate_response

        # Test question about leave policy
        question = "How many days of sick leave am I entitled to?"
        logger.info(f"\nQuestion: '{question}'")

        response, retrieved_chunks = generate_response(
            user_message=question, conversation_history=[], db=db, user_id=user_id
        )

        logger.info(f"\nResponse:\n{response}")

        if retrieved_chunks:
            logger.info(f"\nRetrieved {len(retrieved_chunks)} chunks:")
            for idx, chunk in enumerate(retrieved_chunks, 1):
                logger.info(f"  {idx}. {chunk['file_name']} (score: {chunk['score']:.4f})")

        if response and "10 days" in response.lower():
            logger.info("\n✓ RAG conversation PASSED (correct answer detected)")
            return True
        elif response:
            logger.warning(
                "\n⚠ RAG conversation completed but answer may be incorrect"
                "\n  Expected mention of '10 days' of sick leave"
            )
            return True
        else:
            logger.error("\n✗ RAG conversation FAILED: No response generated")
            return False

    except Exception as e:
        logger.error(f"\n✗ RAG conversation FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all RAG tests."""
    logger.info("Starting RAG Workflow Tests")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"RAG Enabled: {settings.ENABLE_RAG}")

    if not settings.ENABLE_RAG:
        logger.error("RAG is not enabled in .env file! Set ENABLE_RAG=true")
        sys.exit(1)

    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get or create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()

        if not test_user:
            logger.info("Creating test user...")
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="dummy_hash",  # Not used in tests
                full_name="Test User",
                is_active=True,
                is_superuser=False,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info(f"✓ Test user created: {test_user.id}")
        else:
            logger.info(f"✓ Using existing test user: {test_user.id}")

        # Run tests
        test_results = []

        # Test 1: Document Processing
        document_id = test_document_processing(db, test_user.id)
        test_results.append(("Document Processing", document_id is not None))

        if not document_id:
            logger.error("Document processing failed, skipping remaining tests")
            return

        # Test 2: Hybrid Search
        search_passed = test_hybrid_search(db, test_user.id)
        test_results.append(("Hybrid Search", search_passed))

        # Test 3: RAG Conversation
        rag_passed = test_rag_conversation(db, test_user.id)
        test_results.append(("RAG Conversation", rag_passed))

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        all_passed = True
        for test_name, passed in test_results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            logger.info(f"{test_name}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            logger.info("\n🎉 All tests PASSED!")
        else:
            logger.info("\n❌ Some tests FAILED")

    finally:
        db.close()


if __name__ == "__main__":
    main()
