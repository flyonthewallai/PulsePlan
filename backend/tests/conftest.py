import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app
from app.config.settings import settings

# Override settings for testing
settings.ENVIRONMENT = "testing"
settings.ENABLE_RATE_LIMITING = False

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
async def async_client():
    """Async test client for FastAPI app"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_user_id():
    """Mock user ID for testing"""
    return "test-user-12345"

@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzNDUiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJpYXQiOjE2MzA0NDAwMDB9.mock_signature"