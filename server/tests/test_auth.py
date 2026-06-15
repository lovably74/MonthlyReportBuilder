"""Tests for Server-ID token authentication middleware."""

from unittest.mock import patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import verify_server_id
from app.main import app

# Test the actual app's health endpoint (no auth required)
main_client = TestClient(app)

# Create a small test app with a protected route to test the dependency
test_app = FastAPI()


@test_app.get("/protected")
async def protected_route(_: None = Depends(verify_server_id)):
    """A test route protected by Server-ID auth."""
    return {"message": "access granted"}


test_client = TestClient(test_app)

FAKE_SERVER_ID = "12345678-1234-1234-1234-123456789abc"


class TestVerifyServerIdDependency:
    """Tests for the verify_server_id FastAPI dependency."""

    @patch("app.core.auth.get_server_id", return_value=FAKE_SERVER_ID)
    def test_valid_server_id_passes(self, mock_get_id):
        """Valid X-Server-ID header allows the request to proceed."""
        response = test_client.get(
            "/protected",
            headers={"X-Server-ID": FAKE_SERVER_ID},
        )
        assert response.status_code == 200
        assert response.json() == {"message": "access granted"}

    @patch("app.core.auth.get_server_id", return_value=FAKE_SERVER_ID)
    def test_missing_header_returns_401(self, mock_get_id):
        """Missing X-Server-ID header returns 401 Unauthorized."""
        response = test_client.get("/protected")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing Server-ID token"

    @patch("app.core.auth.get_server_id", return_value=FAKE_SERVER_ID)
    def test_invalid_server_id_returns_401(self, mock_get_id):
        """Wrong X-Server-ID header value returns 401 Unauthorized."""
        response = test_client.get(
            "/protected",
            headers={"X-Server-ID": "wrong-id-value"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing Server-ID token"

    @patch("app.core.auth.get_server_id", return_value=FAKE_SERVER_ID)
    def test_empty_server_id_returns_401(self, mock_get_id):
        """Empty X-Server-ID header value returns 401 Unauthorized."""
        response = test_client.get(
            "/protected",
            headers={"X-Server-ID": ""},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing Server-ID token"


class TestHealthEndpointNoAuth:
    """Tests that the /health endpoint works without authentication."""

    def test_health_endpoint_requires_no_auth(self):
        """Health endpoint responds 200 without any X-Server-ID header."""
        response = main_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_endpoint_works_with_invalid_auth(self):
        """Health endpoint responds 200 even with an invalid X-Server-ID header."""
        response = main_client.get(
            "/health",
            headers={"X-Server-ID": "totally-wrong-id"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
