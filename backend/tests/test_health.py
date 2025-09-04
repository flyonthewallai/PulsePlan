import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "PulsePlan API v2.0 - FastAPI Backend"
    assert data["status"] == "operational"

def test_legacy_health_endpoint(client: TestClient):
    """Test legacy health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "pulseplan-fastapi"

def test_api_health_endpoint(client: TestClient):
    """Test API health endpoint"""
    response = client.get("/api/v1/health/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data

def test_readiness_endpoint(client: TestClient):
    """Test readiness probe endpoint"""
    response = client.get("/api/v1/health/ready")
    # May return 200 or 503 depending on dependencies
    assert response.status_code in [200, 503]

def test_liveness_endpoint(client: TestClient):
    """Test liveness probe endpoint"""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"