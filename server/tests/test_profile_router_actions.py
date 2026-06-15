"""Tests for profile router action endpoints (copy, set default, export, import).

Tests cover Task 8.2 endpoints:
- POST /api/v1/profiles/{profile_id}/copy
- PUT /api/v1/profiles/{profile_id}/default
- GET /api/v1/profiles/{profile_id}/export
- POST /api/v1/profiles/import
"""

import json

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.server_identity import get_server_id
from app.main import app


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite async engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create an async session factory and yield a session."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(async_engine):
    """Create a test HTTPX AsyncClient with DB override."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return headers with valid Server-ID token."""
    return {"X-Server-ID": get_server_id()}


async def _create_profile(
    client: AsyncClient, auth_headers: dict, name: str = "Test Profile", description: str = ""
) -> dict:
    """Helper to create a profile via the API."""
    response = await client.post(
        "/api/v1/profiles",
        json={"name": name, "description": description},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


# ─── Copy Endpoint Tests ─────────────────────────────────────────────────────


class TestCopyEndpoint:
    """Tests for POST /api/v1/profiles/{profile_id}/copy."""

    async def test_copy_returns_201_with_correct_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copy returns 201 with name format '원본 (복사본)'."""
        original = await _create_profile(client, auth_headers, name="My Profile")

        response = await client.post(
            f"/api/v1/profiles/{original['id']}/copy",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Profile (복사본)"
        assert data["is_default"] is False
        assert data["id"] != original["id"]

    async def test_copy_preserves_description(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copy preserves the original profile's description."""
        original = await _create_profile(
            client, auth_headers, name="Described", description="Some description"
        )

        response = await client.post(
            f"/api/v1/profiles/{original['id']}/copy",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Some description"

    async def test_copy_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copying a non-existent profile returns 404."""
        response = await client.post(
            "/api/v1/profiles/9999/copy",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_copy_increments_suffix(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Repeated copies increment the suffix number."""
        original = await _create_profile(client, auth_headers, name="Base")

        # First copy
        resp1 = await client.post(
            f"/api/v1/profiles/{original['id']}/copy",
            headers=auth_headers,
        )
        assert resp1.status_code == 201
        assert resp1.json()["name"] == "Base (복사본)"

        # Second copy
        resp2 = await client.post(
            f"/api/v1/profiles/{original['id']}/copy",
            headers=auth_headers,
        )
        assert resp2.status_code == 201
        assert resp2.json()["name"] == "Base (복사본 2)"


# ─── Set Default Endpoint Tests ──────────────────────────────────────────────


class TestSetDefaultEndpoint:
    """Tests for PUT /api/v1/profiles/{profile_id}/default."""

    async def test_set_default_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Setting default returns 200 with the updated profile."""
        # First profile is auto-default
        first = await _create_profile(client, auth_headers, name="First")
        second = await _create_profile(client, auth_headers, name="Second")

        response = await client.put(
            f"/api/v1/profiles/{second['id']}/default",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == second["id"]
        assert data["is_default"] is True

    async def test_set_default_unsets_previous(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Setting new default unsets the previous default profile."""
        first = await _create_profile(client, auth_headers, name="First")
        second = await _create_profile(client, auth_headers, name="Second")

        # Set second as default
        await client.put(
            f"/api/v1/profiles/{second['id']}/default",
            headers=auth_headers,
        )

        # Check first is no longer default
        resp = await client.get(
            f"/api/v1/profiles/{first['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_default"] is False

    async def test_set_default_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Setting default on non-existent profile returns 404."""
        response = await client.put(
            "/api/v1/profiles/9999/default",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ─── Export Endpoint Tests ───────────────────────────────────────────────────


class TestExportEndpoint:
    """Tests for GET /api/v1/profiles/{profile_id}/export."""

    async def test_export_returns_correct_json_structure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Export returns JSON with version, exported_at, profile, and settings."""
        profile = await _create_profile(
            client, auth_headers, name="Export Test", description="desc"
        )

        response = await client.get(
            f"/api/v1/profiles/{profile['id']}/export",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert data["version"] == "1.0"
        assert "exported_at" in data
        assert "profile" in data
        assert "settings" in data

        # Verify profile data
        assert data["profile"]["name"] == "Export Test"
        assert data["profile"]["description"] == "desc"

        # Verify settings structure
        assert "document_type_configs" in data["settings"]
        assert "folder_configs" in data["settings"]
        assert "template_mappings" in data["settings"]

    async def test_export_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Exporting non-existent profile returns 404."""
        response = await client.get(
            "/api/v1/profiles/9999/export",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ─── Import Endpoint Tests ───────────────────────────────────────────────────


class TestImportEndpoint:
    """Tests for POST /api/v1/profiles/import."""

    async def test_import_creates_profile_from_json(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Import creates a new profile from valid JSON body."""
        import_data = {
            "version": "1.0",
            "exported_at": "2024-01-01T00:00:00",
            "profile": {
                "name": "Imported Profile",
                "description": "Imported desc",
                "is_default": False,
            },
            "settings": {
                "document_type_configs": [],
                "folder_configs": [],
                "template_mappings": [],
            },
        }

        response = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps(import_data),
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Imported Profile"
        assert data["description"] == "Imported desc"
        assert data["id"] is not None

    async def test_import_rejects_oversized_payload(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Import rejects payload exceeding 10MB."""
        # Simulate large content-length header
        response = await client.post(
            "/api/v1/profiles/import",
            content=b'{"profile": {"name": "x"}}',
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Content-Length": str(11 * 1024 * 1024),  # 11MB
            },
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "IMPORT_FILE_TOO_LARGE"

    async def test_import_rejects_invalid_json(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Import rejects invalid JSON body."""
        response = await client.post(
            "/api/v1/profiles/import",
            content=b"not valid json {{{",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "IMPORT_INVALID_JSON"

    async def test_import_rejects_missing_profile_key(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Import rejects JSON missing the 'profile' key."""
        response = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps({"version": "1.0"}).encode(),
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 400

    async def test_import_rejects_missing_name_field(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Import rejects JSON with profile missing 'name' field."""
        import_data = {
            "version": "1.0",
            "profile": {
                "description": "no name here",
            },
        }

        response = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps(import_data).encode(),
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 400
