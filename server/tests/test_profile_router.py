"""Integration tests for Profile CRUD API router endpoints.

Tests cover:
- POST /api/v1/profiles → 201
- GET /api/v1/profiles → 200 (list)
- GET /api/v1/profiles/{id} → 200 (detail)
- PUT /api/v1/profiles/{id} → 200 (update)
- DELETE /api/v1/profiles/{id} → 204 (no content)
- Error codes: 404, 409, 400, 422, 401
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

FAKE_SERVER_ID = "12345678-1234-1234-1234-123456789abc"


@pytest.fixture
async def async_session():
    """Create an in-memory SQLite database and yield an async session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def override_deps(async_session: AsyncSession):
    """Override FastAPI dependencies for testing."""

    async def _override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return headers with a valid Server-ID."""
    return {"X-Server-ID": FAKE_SERVER_ID}


@pytest.fixture
async def client(override_deps):
    """Create an async test client with dependency overrides and mocked auth."""
    with patch("app.core.auth.get_server_id", return_value=FAKE_SERVER_ID):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class TestCreateProfile:
    """Tests for POST /api/v1/profiles."""

    async def test_create_returns_201(self, client: AsyncClient, auth_headers):
        """Creating a valid profile returns 201 with profile data."""
        response = await client.post(
            "/api/v1/profiles",
            json={"name": "New Profile", "description": "A test profile"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "New Profile"
        assert body["description"] == "A test profile"
        assert body["is_default"] is True  # First profile is auto-default
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body

    async def test_create_second_profile_not_default(
        self, client: AsyncClient, auth_headers
    ):
        """Second profile should not be default."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "First"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/profiles",
            json={"name": "Second"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["is_default"] is False

    async def test_create_duplicate_name_returns_409(
        self, client: AsyncClient, auth_headers
    ):
        """Creating with a duplicate name returns 409 Conflict."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "Duplicate"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/profiles",
            json={"name": "Duplicate"},
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_NAME_DUPLICATE"

    async def test_create_empty_name_returns_422(
        self, client: AsyncClient, auth_headers
    ):
        """Creating with an empty name returns 422 Validation Error."""
        response = await client.post(
            "/api/v1/profiles",
            json={"name": "   "},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_missing_name_returns_422(
        self, client: AsyncClient, auth_headers
    ):
        """Creating without a name field returns 422 Validation Error."""
        response = await client.post(
            "/api/v1/profiles",
            json={"description": "no name"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        """Request without Server-ID header returns 401."""
        response = await client.post(
            "/api/v1/profiles",
            json={"name": "NoAuth"},
        )
        assert response.status_code == 401


class TestGetProfile:
    """Tests for GET /api/v1/profiles/{profile_id}."""

    async def test_get_returns_profile(self, client: AsyncClient, auth_headers):
        """Getting an existing profile returns 200 with profile data."""
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "GetMe", "description": "test desc"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/profiles/{profile_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == profile_id
        assert body["name"] == "GetMe"
        assert body["description"] == "test desc"

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers
    ):
        """Getting a non-existent profile returns 404."""
        response = await client.get(
            "/api/v1/profiles/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_NOT_FOUND"


class TestListProfiles:
    """Tests for GET /api/v1/profiles."""

    async def test_list_empty_returns_empty(
        self, client: AsyncClient, auth_headers
    ):
        """Listing profiles when none exist returns empty list."""
        response = await client.get("/api/v1/profiles", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["profiles"] == []
        assert body["total"] == 0

    async def test_list_returns_profiles(
        self, client: AsyncClient, auth_headers
    ):
        """Listing profiles returns all created profiles."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "Profile A"},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/profiles",
            json={"name": "Profile B"},
            headers=auth_headers,
        )

        response = await client.get("/api/v1/profiles", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["profiles"]) == 2

    async def test_list_default_first(self, client: AsyncClient, auth_headers):
        """Default profile should be first in the list."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "Default One"},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/profiles",
            json={"name": "Second"},
            headers=auth_headers,
        )

        response = await client.get("/api/v1/profiles", headers=auth_headers)
        body = response.json()
        assert body["profiles"][0]["name"] == "Default One"
        assert body["profiles"][0]["is_default"] is True


class TestUpdateProfile:
    """Tests for PUT /api/v1/profiles/{profile_id}."""

    async def test_update_returns_updated_profile(
        self, client: AsyncClient, auth_headers
    ):
        """Updating a profile returns 200 with the updated data."""
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Original", "description": "old desc"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/profiles/{profile_id}",
            json={"name": "Updated", "description": "new desc"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Updated"
        assert body["description"] == "new desc"

    async def test_update_partial_name_only(
        self, client: AsyncClient, auth_headers
    ):
        """Updating only the name preserves the description."""
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Prof", "description": "keep me"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/profiles/{profile_id}",
            json={"name": "NewName"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "NewName"
        assert response.json()["description"] == "keep me"

    async def test_update_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers
    ):
        """Updating a non-existent profile returns 404."""
        response = await client.put(
            "/api/v1/profiles/9999",
            json={"name": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_NOT_FOUND"

    async def test_update_duplicate_name_returns_409(
        self, client: AsyncClient, auth_headers
    ):
        """Updating to a conflicting name returns 409."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "Existing"},
            headers=auth_headers,
        )
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "ToUpdate"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/profiles/{profile_id}",
            json={"name": "Existing"},
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_NAME_DUPLICATE"

    async def test_update_refreshes_updated_at(
        self, client: AsyncClient, auth_headers
    ):
        """Updating a profile refreshes its updated_at timestamp."""
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Timestamp"},
            headers=auth_headers,
        )
        original_updated_at = create_resp.json()["updated_at"]
        profile_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/profiles/{profile_id}",
            json={"description": "changed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["updated_at"] >= original_updated_at


class TestDeleteProfile:
    """Tests for DELETE /api/v1/profiles/{profile_id}."""

    async def test_delete_returns_204(self, client: AsyncClient, auth_headers):
        """Deleting a profile returns 204 No Content."""
        # Create two profiles (cannot delete the last one)
        await client.post(
            "/api/v1/profiles",
            json={"name": "Keep"},
            headers=auth_headers,
        )
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "ToDelete"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/profiles/{profile_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_delete_removes_profile(
        self, client: AsyncClient, auth_headers
    ):
        """Deleted profile is no longer accessible."""
        await client.post(
            "/api/v1/profiles",
            json={"name": "Stay"},
            headers=auth_headers,
        )
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Gone"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        await client.delete(
            f"/api/v1/profiles/{profile_id}",
            headers=auth_headers,
        )

        get_resp = await client.get(
            f"/api/v1/profiles/{profile_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers
    ):
        """Deleting a non-existent profile returns 404."""
        response = await client.delete(
            "/api/v1/profiles/9999",
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_NOT_FOUND"

    async def test_delete_last_profile_returns_400(
        self, client: AsyncClient, auth_headers
    ):
        """Deleting the last remaining profile returns 400."""
        create_resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Only One"},
            headers=auth_headers,
        )
        profile_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/profiles/{profile_id}",
            headers=auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "PROFILE_LAST_DELETE"

    async def test_delete_without_auth_returns_401(self, client: AsyncClient):
        """Delete without Server-ID header returns 401."""
        response = await client.delete("/api/v1/profiles/1")
        assert response.status_code == 401
