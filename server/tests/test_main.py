"""Tests for the FastAPI application startup and health check."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """서버 상태 확인 엔드포인트가 정상 응답하는지 검증."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_headers():
    """CORS 헤더가 LAN 접근을 허용하도록 설정되어 있는지 검증."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://192.168.1.100:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_app_metadata():
    """FastAPI 앱 메타데이터가 올바르게 설정되어 있는지 검증."""
    assert app.title == "CM Report Server"
    assert app.version == "0.1.0"
