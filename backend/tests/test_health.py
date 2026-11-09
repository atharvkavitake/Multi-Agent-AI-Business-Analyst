"""
Unit and Integration Tests for FastAPI Core and Health Check Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import get_settings

settings = get_settings()


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client properly managing the FastAPI lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify that the root endpoint returns 200 and API documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert data["status"] == "online"
    assert "documentation" in data
    assert data["documentation"]["swagger_ui"] == "/docs"


def test_health_check_endpoint(client):
    """Verify that the health check endpoint returns 200 and component statuses."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert data["environment"] == settings.ENVIRONMENT
    assert "components" in data
    assert data["components"]["database"] in ["online", "offline"]
    assert "ai_settings" in data


def test_cors_headers(client):
    """Verify that CORS middleware attaches appropriate headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_frontend_static_serving(client):
    """Verify that the frontend web application is mounted and served at /app/."""
    response = client.get("/app/")
    assert response.status_code == 200
    assert "Multi-Agent AI Business Analyst" in response.text

