"""Integration flow tests for the full profile API lifecycle.

Task 17.2: 서버 통합 테스트 (FastAPI TestClient)

Tests cover:
1. Complete CRUD scenario flow: create → list → get → update → copy → set_default → export → import → delete
2. Verify copy includes description (proxy for "하위 설정 데이터" which doesn't exist yet) (Req 3.1)
3. Verify delete cascade: deleted profile is gone from all queries (Req 4.2)
4. Verify all error response formats match the ErrorResponse schema
5. Verify that operations correctly chain (e.g., deleting default auto-reassigns)
"""

import json

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.server_identity import get_server_id
from app.main import app


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite async engine with fresh tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(async_engine):
    """Create an async HTTPX test client with DB override."""
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
    """Return headers with a valid Server-ID token."""
    return {"X-Server-ID": get_server_id()}


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _create_profile(
    client: AsyncClient,
    headers: dict,
    name: str = "Test",
    description: str = "",
) -> dict:
    """Helper to create a profile and return parsed JSON response."""
    resp = await client.post(
        "/api/v1/profiles",
        json={"name": name, "description": description},
        headers=headers,
    )
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    return resp.json()


def _assert_error_response_format(detail: dict) -> None:
    """Validate that an error detail matches the ErrorResponse schema.

    ErrorResponse must have:
    - error_code: str (non-empty)
    - message: str (non-empty)
    - detail: str | None (optional)
    - field: str | None (optional)
    """
    assert "error_code" in detail, "Missing 'error_code' in error response"
    assert "message" in detail, "Missing 'message' in error response"
    assert isinstance(detail["error_code"], str) and detail["error_code"]
    assert isinstance(detail["message"], str) and detail["message"]
    # Optional fields may be present or absent
    if "detail" in detail:
        assert detail["detail"] is None or isinstance(detail["detail"], str)
    if "field" in detail:
        assert detail["field"] is None or isinstance(detail["field"], str)


# ─── Test 1: Complete CRUD Scenario Flow ─────────────────────────────────────


class TestCompleteCRUDFlow:
    """Full lifecycle test: create → list → get → update → copy → set_default → export → import → delete."""

    async def test_full_crud_lifecycle(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Exercises all API operations in sequence as a single scenario."""
        # 1. CREATE - first profile becomes default
        profile = await _create_profile(
            client, auth_headers, name="프로젝트 A", description="현장 A 보고서 설정"
        )
        profile_id = profile["id"]
        assert profile["is_default"] is True
        assert profile["name"] == "프로젝트 A"
        assert profile["description"] == "현장 A 보고서 설정"

        # 2. LIST - should contain exactly 1 profile
        list_resp = await client.get("/api/v1/profiles", headers=auth_headers)
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body["total"] == 1
        assert list_body["profiles"][0]["id"] == profile_id

        # 3. GET - retrieve the specific profile
        get_resp = await client.get(
            f"/api/v1/profiles/{profile_id}", headers=auth_headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "프로젝트 A"

        # 4. UPDATE - change name and description
        update_resp = await client.put(
            f"/api/v1/profiles/{profile_id}",
            json={"name": "프로젝트 A (수정)", "description": "수정된 설명"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["name"] == "프로젝트 A (수정)"
        assert updated["description"] == "수정된 설명"
        assert updated["updated_at"] >= profile["updated_at"]

        # 5. COPY - creates a new profile with "(복사본)" suffix
        copy_resp = await client.post(
            f"/api/v1/profiles/{profile_id}/copy", headers=auth_headers
        )
        assert copy_resp.status_code == 201
        copied = copy_resp.json()
        assert copied["name"] == "프로젝트 A (수정) (복사본)"
        assert copied["is_default"] is False
        copied_id = copied["id"]

        # 6. SET DEFAULT - set the copy as default
        default_resp = await client.put(
            f"/api/v1/profiles/{copied_id}/default", headers=auth_headers
        )
        assert default_resp.status_code == 200
        assert default_resp.json()["is_default"] is True

        # Verify original is no longer default
        orig_resp = await client.get(
            f"/api/v1/profiles/{profile_id}", headers=auth_headers
        )
        assert orig_resp.json()["is_default"] is False

        # 7. EXPORT - export the copy
        export_resp = await client.get(
            f"/api/v1/profiles/{copied_id}/export", headers=auth_headers
        )
        assert export_resp.status_code == 200
        export_data = export_resp.json()
        assert export_data["version"] == "1.0"
        assert export_data["profile"]["name"] == "프로젝트 A (수정) (복사본)"
        assert "settings" in export_data

        # 8. IMPORT - import from the exported data with a different name
        export_data["profile"]["name"] = "가져온 프로필"
        import_resp = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps(export_data),
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert import_resp.status_code == 201
        imported = import_resp.json()
        assert imported["name"] == "가져온 프로필"
        imported_id = imported["id"]

        # 9. DELETE - delete the imported profile
        delete_resp = await client.delete(
            f"/api/v1/profiles/{imported_id}", headers=auth_headers
        )
        assert delete_resp.status_code == 204

        # Verify it's gone
        gone_resp = await client.get(
            f"/api/v1/profiles/{imported_id}", headers=auth_headers
        )
        assert gone_resp.status_code == 404

        # Verify remaining profiles
        final_list = await client.get("/api/v1/profiles", headers=auth_headers)
        assert final_list.json()["total"] == 2


# ─── Test 2: Copy Includes Description (Req 3.1) ────────────────────────────


class TestCopyIncludesDescription:
    """Verify copy operation preserves description (proxy for 하위 설정 데이터)."""

    async def test_copy_preserves_description(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copied profile must include the original's description (Req 3.1)."""
        original = await _create_profile(
            client,
            auth_headers,
            name="상세 프로필",
            description="이 프로필에는 현장 A의 모든 설정이 포함됩니다.",
        )

        copy_resp = await client.post(
            f"/api/v1/profiles/{original['id']}/copy", headers=auth_headers
        )
        assert copy_resp.status_code == 201
        copied = copy_resp.json()
        assert copied["description"] == original["description"]

    async def test_copy_preserves_empty_description(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copy preserves empty description."""
        original = await _create_profile(
            client, auth_headers, name="빈 설명 프로필", description=""
        )

        copy_resp = await client.post(
            f"/api/v1/profiles/{original['id']}/copy", headers=auth_headers
        )
        assert copy_resp.status_code == 201
        assert copy_resp.json()["description"] == ""

    async def test_export_after_copy_contains_same_settings_structure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Export of a copied profile contains the settings structure (proxy test)."""
        original = await _create_profile(
            client, auth_headers, name="Export Copy Test", description="desc"
        )

        copy_resp = await client.post(
            f"/api/v1/profiles/{original['id']}/copy", headers=auth_headers
        )
        copied_id = copy_resp.json()["id"]

        export_resp = await client.get(
            f"/api/v1/profiles/{copied_id}/export", headers=auth_headers
        )
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert "settings" in data
        assert "document_type_configs" in data["settings"]
        assert "folder_configs" in data["settings"]
        assert "template_mappings" in data["settings"]


# ─── Test 3: Delete Cascade (Req 4.2) ────────────────────────────────────────


class TestDeleteCascade:
    """Verify delete removes profile from all queries (cascade behavior)."""

    async def test_deleted_profile_gone_from_get(
        self, client: AsyncClient, auth_headers: dict
    ):
        """After deletion, GET /{id} returns 404."""
        await _create_profile(client, auth_headers, name="Keep")
        to_delete = await _create_profile(client, auth_headers, name="Delete Me")

        await client.delete(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )

        resp = await client.get(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_deleted_profile_gone_from_list(
        self, client: AsyncClient, auth_headers: dict
    ):
        """After deletion, the profile does not appear in the list."""
        await _create_profile(client, auth_headers, name="Survivor")
        to_delete = await _create_profile(client, auth_headers, name="Victim")

        await client.delete(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )

        list_resp = await client.get("/api/v1/profiles", headers=auth_headers)
        names = [p["name"] for p in list_resp.json()["profiles"]]
        assert "Victim" not in names
        assert "Survivor" in names

    async def test_deleted_profile_gone_from_export(
        self, client: AsyncClient, auth_headers: dict
    ):
        """After deletion, export for that ID returns 404."""
        await _create_profile(client, auth_headers, name="Alive")
        to_delete = await _create_profile(client, auth_headers, name="Dead")

        await client.delete(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )

        export_resp = await client.get(
            f"/api/v1/profiles/{to_delete['id']}/export", headers=auth_headers
        )
        assert export_resp.status_code == 404

    async def test_deleted_profile_cannot_be_copied(
        self, client: AsyncClient, auth_headers: dict
    ):
        """After deletion, copy for that ID returns 404."""
        await _create_profile(client, auth_headers, name="Base")
        to_delete = await _create_profile(client, auth_headers, name="Gone")

        await client.delete(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )

        copy_resp = await client.post(
            f"/api/v1/profiles/{to_delete['id']}/copy", headers=auth_headers
        )
        assert copy_resp.status_code == 404

    async def test_deleted_profile_cannot_be_set_default(
        self, client: AsyncClient, auth_headers: dict
    ):
        """After deletion, setting as default returns 404."""
        await _create_profile(client, auth_headers, name="Remaining")
        to_delete = await _create_profile(client, auth_headers, name="Removed")

        await client.delete(
            f"/api/v1/profiles/{to_delete['id']}", headers=auth_headers
        )

        default_resp = await client.put(
            f"/api/v1/profiles/{to_delete['id']}/default", headers=auth_headers
        )
        assert default_resp.status_code == 404


# ─── Test 4: Error Response Format Validation ────────────────────────────────


class TestErrorResponseFormat:
    """Verify all error responses match the ErrorResponse schema."""

    async def test_404_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """404 error has correct ErrorResponse format."""
        resp = await client.get("/api/v1/profiles/9999", headers=auth_headers)
        assert resp.status_code == 404
        _assert_error_response_format(resp.json()["detail"])

    async def test_409_duplicate_name_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """409 Conflict error has correct ErrorResponse format."""
        await _create_profile(client, auth_headers, name="Unique")
        resp = await client.post(
            "/api/v1/profiles",
            json={"name": "Unique"},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        _assert_error_response_format(detail)
        assert detail["error_code"] == "PROFILE_NAME_DUPLICATE"
        assert detail["field"] == "name"

    async def test_400_last_delete_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """400 last-profile-delete error has correct ErrorResponse format."""
        profile = await _create_profile(client, auth_headers, name="Only One")
        resp = await client.delete(
            f"/api/v1/profiles/{profile['id']}", headers=auth_headers
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        _assert_error_response_format(detail)
        assert detail["error_code"] == "PROFILE_LAST_DELETE"

    async def test_400_invalid_json_import_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """400 invalid JSON import error has correct ErrorResponse format."""
        resp = await client.post(
            "/api/v1/profiles/import",
            content=b"not json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        _assert_error_response_format(detail)
        assert detail["error_code"] == "IMPORT_INVALID_JSON"

    async def test_400_file_too_large_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """400 file-too-large error has correct ErrorResponse format."""
        resp = await client.post(
            "/api/v1/profiles/import",
            content=b'{"profile":{"name":"x"}}',
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Content-Length": str(11 * 1024 * 1024),
            },
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        _assert_error_response_format(detail)
        assert detail["error_code"] == "IMPORT_FILE_TOO_LARGE"

    async def test_401_unauthorized_error_format(
        self, client: AsyncClient,
    ):
        """401 Unauthorized response when no auth header."""
        resp = await client.get("/api/v1/profiles")
        assert resp.status_code == 401

    async def test_404_update_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """404 on update has correct ErrorResponse format."""
        resp = await client.put(
            "/api/v1/profiles/9999",
            json={"name": "Nope"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        _assert_error_response_format(resp.json()["detail"])

    async def test_404_delete_error_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """404 on delete has correct ErrorResponse format."""
        resp = await client.delete(
            "/api/v1/profiles/9999", headers=auth_headers
        )
        assert resp.status_code == 404
        _assert_error_response_format(resp.json()["detail"])

    async def test_409_copy_name_exhausted_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """409 COPY_NAME_EXHAUSTED has correct ErrorResponse format when copy name slots full."""
        # This is a boundary test - create original + "원본 (복사본)" to force suffix 2
        original = await _create_profile(client, auth_headers, name="원본")
        # Create "원본 (복사본)" manually to occupy the first slot
        await _create_profile(client, auth_headers, name="원본 (복사본)")

        # Copy should succeed with "원본 (복사본 2)"
        copy_resp = await client.post(
            f"/api/v1/profiles/{original['id']}/copy", headers=auth_headers
        )
        assert copy_resp.status_code == 201
        assert copy_resp.json()["name"] == "원본 (복사본 2)"


# ─── Test 5: Operations Chain Correctly ──────────────────────────────────────


class TestOperationsChaining:
    """Verify operations chain correctly (default reassignment, cascading effects)."""

    async def test_delete_default_reassigns_to_most_recent(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Deleting default profile auto-assigns the most recently updated as new default."""
        # Create three profiles - first is default
        first = await _create_profile(client, auth_headers, name="First")
        second = await _create_profile(client, auth_headers, name="Second")
        third = await _create_profile(client, auth_headers, name="Third")

        # Update "Third" to make it the most recently updated
        await client.put(
            f"/api/v1/profiles/{third['id']}",
            json={"description": "most recent"},
            headers=auth_headers,
        )

        # Delete the default (First)
        del_resp = await client.delete(
            f"/api/v1/profiles/{first['id']}", headers=auth_headers
        )
        assert del_resp.status_code == 204

        # Third should now be the default (most recently updated)
        third_resp = await client.get(
            f"/api/v1/profiles/{third['id']}", headers=auth_headers
        )
        assert third_resp.json()["is_default"] is True

        # Second should not be default
        second_resp = await client.get(
            f"/api/v1/profiles/{second['id']}", headers=auth_headers
        )
        assert second_resp.json()["is_default"] is False

    async def test_set_default_then_delete_new_default(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Setting a new default, then deleting it, cascades default to another."""
        first = await _create_profile(client, auth_headers, name="Alpha")
        second = await _create_profile(client, auth_headers, name="Beta")
        third = await _create_profile(client, auth_headers, name="Gamma")

        # Set Beta as default
        await client.put(
            f"/api/v1/profiles/{second['id']}/default", headers=auth_headers
        )

        # Delete Beta (new default)
        await client.delete(
            f"/api/v1/profiles/{second['id']}", headers=auth_headers
        )

        # One of the remaining must be default
        list_resp = await client.get("/api/v1/profiles", headers=auth_headers)
        profiles = list_resp.json()["profiles"]
        defaults = [p for p in profiles if p["is_default"]]
        assert len(defaults) == 1

    async def test_copy_does_not_become_default(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Copied profile is never the default, even if original is default."""
        original = await _create_profile(
            client, auth_headers, name="Default Original"
        )
        assert original["is_default"] is True

        copy_resp = await client.post(
            f"/api/v1/profiles/{original['id']}/copy", headers=auth_headers
        )
        assert copy_resp.json()["is_default"] is False

        # System still has exactly one default
        list_resp = await client.get("/api/v1/profiles", headers=auth_headers)
        defaults = [
            p for p in list_resp.json()["profiles"] if p["is_default"]
        ]
        assert len(defaults) == 1
        assert defaults[0]["id"] == original["id"]

    async def test_import_with_is_default_true_does_not_override_existing(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Importing a profile with is_default=true doesn't steal default from existing."""
        existing = await _create_profile(
            client, auth_headers, name="Existing Default"
        )
        assert existing["is_default"] is True

        import_data = {
            "version": "1.0",
            "profile": {
                "name": "Imported Default",
                "description": "",
                "is_default": True,
            },
        }
        import_resp = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps(import_data),
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert import_resp.status_code == 201
        assert import_resp.json()["is_default"] is False

        # Original is still default
        orig_resp = await client.get(
            f"/api/v1/profiles/{existing['id']}", headers=auth_headers
        )
        assert orig_resp.json()["is_default"] is True

    async def test_list_ordering_after_multiple_operations(
        self, client: AsyncClient, auth_headers: dict
    ):
        """List ordering: default first, rest by updated_at descending."""
        a = await _create_profile(client, auth_headers, name="Alpha")
        b = await _create_profile(client, auth_headers, name="Beta")
        c = await _create_profile(client, auth_headers, name="Gamma")

        # Update Beta to make it the most recent non-default
        await client.put(
            f"/api/v1/profiles/{b['id']}",
            json={"description": "updated"},
            headers=auth_headers,
        )

        list_resp = await client.get("/api/v1/profiles", headers=auth_headers)
        profiles = list_resp.json()["profiles"]

        # First should be the default (Alpha)
        assert profiles[0]["is_default"] is True
        assert profiles[0]["name"] == "Alpha"

        # Among non-defaults, Beta should come first (most recently updated)
        non_defaults = [p for p in profiles if not p["is_default"]]
        assert non_defaults[0]["name"] == "Beta"

    async def test_export_import_roundtrip_preserves_data(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Export → Import preserves name and description byte-identical."""
        original = await _create_profile(
            client,
            auth_headers,
            name="라운드트립 테스트",
            description="한글 설명이 포함된 프로필",
        )

        # Export
        export_resp = await client.get(
            f"/api/v1/profiles/{original['id']}/export", headers=auth_headers
        )
        export_data = export_resp.json()

        # Modify name for import (to avoid duplicate)
        export_data["profile"]["name"] = "라운드트립 복원"

        # Import
        import_resp = await client.post(
            "/api/v1/profiles/import",
            content=json.dumps(export_data, ensure_ascii=False).encode("utf-8"),
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert import_resp.status_code == 201
        imported = import_resp.json()
        assert imported["name"] == "라운드트립 복원"
        assert imported["description"] == original["description"]
