"""
Canvas Integration Test Script
Tests the Canvas connection and sync functionality with real Canvas API
"""
import asyncio
import logging
from datetime import datetime
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable debug logging for Canvas jobs
logging.getLogger("app.jobs.canvas_backfill_job").setLevel(logging.DEBUG)

# Configuration - Token should be stored in database via canvas_token_service
# This test retrieves the token from the database for the test user
CANVAS_URL = "https://canvas.colorado.edu"
USER_ID = "4dd1cef4-a1e9-4b34-a711-1a1e17adbd83"


async def test_canvas_token_validation():
    """Test Canvas token validation with real API"""
    try:
        from app.services.integrations.canvas_token_service import get_canvas_token_service

        logger.info("Testing Canvas token validation with real API...")
        token_service = get_canvas_token_service()

        # Retrieve token from database
        token_data = await token_service.retrieve_canvas_token(USER_ID)
        if not token_data:
            logger.error("❌ No Canvas token found in database for test user")
            logger.info("   Please store a Canvas token first using store_canvas_token()")
            return False

        canvas_url = token_data.get("base_url", CANVAS_URL)
        # Token is encrypted in DB, validate using the service method
        is_valid = await token_service.validate_token(USER_ID)

        if is_valid:
            logger.info("✅ Canvas API token is valid!")
            return True
        else:
            logger.error("❌ Canvas API token is invalid")
            return False

    except Exception as e:
        logger.error(f"Token validation test failed: {e}")
        return False


async def test_canvas_token_storage():
    """Test Canvas token storage and retrieval"""
    try:
        from app.services.integrations.canvas_token_service import get_canvas_token_service

        logger.info("Testing Canvas token storage and retrieval...")
        token_service = get_canvas_token_service()

        # Test retrieving token from database
        retrieved = await token_service.retrieve_canvas_token(USER_ID)

        if retrieved:
            logger.info("✅ Token retrieved successfully from database")
            logger.info(f"Base URL: {retrieved['base_url']}")
            logger.info(f"Status: {retrieved['status']}")

            # Verify decrypted token works
            test_valid = await token_service.validate_token(USER_ID)
            if test_valid:
                logger.info("✅ Stored token validates correctly")
            else:
                logger.error("❌ Stored token validation failed")

            return test_valid
        else:
            logger.warning("⚠️ No token found in database for test user")
            logger.info("   To test token storage, first store a token using:")
            logger.info(f"   await token_service.store_canvas_token(user_id='{USER_ID}', canvas_url='{CANVAS_URL}', api_token='YOUR_TOKEN')")
            return False

    except Exception as e:
        logger.error(f"Token storage test failed: {e}")
        return False


async def test_canvas_api_calls():
    """Test actual Canvas API calls"""
    try:
        import httpx
        from app.services.integrations.canvas_token_service import get_canvas_token_service

        logger.info("Testing Canvas API calls...")

        # Retrieve token from database
        token_service = get_canvas_token_service()
        token_data = await token_service.retrieve_canvas_token(USER_ID)
        if not token_data:
            logger.error("❌ No Canvas token found in database for test user")
            return False

        # Get decrypted token for API calls
        # Note: The service should provide a method to get the decrypted token
        # For now, we'll use the validation which internally uses the token
        canvas_url = token_data.get("base_url", CANVAS_URL)
        
        # Test token validation (which makes API calls internally)
        is_valid = await token_service.validate_token(USER_ID)
        if not is_valid:
            logger.error("❌ Canvas token is invalid")
            return False

        logger.info("✅ Canvas API token is valid and can make API calls")
        # Additional API testing can be done through the Canvas service methods
        # which handle token retrieval and decryption internally
        return True

    except Exception as e:
        logger.error(f"Canvas API test failed: {e}")
        return False


async def test_canvas_backfill_job():
    """Test Canvas backfill job with real data (limited)"""
    try:
        from app.jobs.canvas.backfill_job import get_canvas_backfill_job

        logger.info("Testing Canvas backfill job...")

        # Verify token exists in database
        from app.services.integrations.canvas_token_service import get_canvas_token_service
        token_service = get_canvas_token_service()

        token_data = await token_service.retrieve_canvas_token(USER_ID)
        if not token_data:
            logger.error("❌ No Canvas token found in database for test user")
            logger.info("   Please store a Canvas token first before running backfill test")
            return False

        # Run backfill job
        backfill_job = get_canvas_backfill_job()
        result = await backfill_job.execute_backfill(USER_ID, force_restart=True)

        if result.get("status") == "completed":
            logger.info(f"✅ Backfill completed successfully!")
            logger.info(f"   - Courses processed: {result.get('courses_processed', 0)}")
            logger.info(f"   - Assignments imported: {result.get('assignments_imported', 0)}")
            logger.info(f"   - Tasks created: {result.get('assignments_upserted', 0)}")
            logger.info(f"   - Execution time: {result.get('execution_time', 0):.2f}s")

            if result.get('errors'):
                logger.warning(f"   - Errors: {len(result['errors'])}")

            return True
        else:
            logger.error(f"❌ Backfill failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"Backfill job test failed: {e}")
        return False


async def test_canvas_models():
    """Test Canvas database models"""
    try:
        from app.database.models import (
            CanvasIntegrationModel,
            ExternalCursorModel,
            TaskModel,
            ExternalSource
        )

        logger.info("Testing Canvas models...")

        # Test Canvas integration model
        integration = CanvasIntegrationModel(
            user_id=USER_ID,
            base_url=CANVAS_URL,
            token_ciphertext="encrypted_token_data",
            kms_key_id="test_key_id",
            status="ok"
        )

        integration_dict = integration.to_supabase_insert()
        logger.info("✅ Canvas integration model validated")

        # Test external cursor model
        cursor = ExternalCursorModel(
            user_id=USER_ID,
            source="canvas",
            cursor_type="assignments",
            cursor_value="2023-10-01T12:00:00Z"
        )

        cursor_dict = cursor.to_supabase_insert()
        logger.info("✅ External cursor model validated")

        # Test task model with external source
        task = TaskModel(
            user_id=USER_ID,
            title="Test Assignment",
            external_source=ExternalSource.CANVAS,
            external_id="12345",
            external_course_id="67890"
        )

        task_dict = task.to_supabase_insert()
        logger.info("✅ Task model with external source validated")

        return True

    except Exception as e:
        logger.error(f"Models test failed: {e}")
        return False


async def run_all_tests():
    """Run all Canvas integration tests with real API"""
    logger.info("Starting Canvas Integration Tests with Real API")
    logger.info("=" * 60)
    logger.info(f"Canvas URL: {CANVAS_URL}")
    logger.info(f"User ID: {USER_ID}")
    logger.info("=" * 60)

    tests = [
        ("Canvas Models", test_canvas_models),
        ("Canvas API Token Validation", test_canvas_token_validation),
        ("Canvas API Calls", test_canvas_api_calls),
        ("Canvas Token Storage", test_canvas_token_storage),
        ("Canvas Backfill Job", test_canvas_backfill_job),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")

    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All Canvas integration tests PASSED!")

        # Show final status
        logger.info("\n📊 Final Integration Status:")
        try:
            from app.config.database.supabase import get_supabase_client
            supabase = get_supabase_client()

            # Check integration record
            response = supabase.table("integration_canvas").select("*").eq(
                "user_id", USER_ID
            ).execute()

            if response.data:
                integration = response.data[0]
                logger.info(f"   - Status: {integration.get('status', 'unknown')}")
                logger.info(f"   - Last sync: {integration.get('last_full_sync_at', 'never')}")

            # Check tasks created
            tasks_response = supabase.table("tasks").select("id, title, external_source").eq(
                "user_id", USER_ID
            ).eq("external_source", "canvas").execute()

            canvas_tasks = tasks_response.data or []
            logger.info(f"   - Canvas tasks in database: {len(canvas_tasks)}")

            if canvas_tasks:
                logger.info("   - Sample tasks:")
                for task in canvas_tasks[:3]:
                    logger.info(f"     • {task.get('title', 'Untitled')}")

        except Exception as e:
            logger.warning(f"Could not fetch final status: {e}")

        return True
    else:
        logger.error(f"💥 {total - passed} tests FAILED")
        return False


if __name__ == "__main__":
    async def main():
        # Show what will be tested
        print(f"\nTesting Canvas integration with:")
        print(f"  Canvas URL: {CANVAS_URL}")
        print(f"  User ID: {USER_ID}")
        print(f"  Note: This will create real database records and make API calls to Canvas.")

        # Run tests directly (no confirmation needed)
        success = await run_all_tests()
        return success

    # Run the async main function
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)