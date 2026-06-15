"""Tests for ProfileService export/import logic and generate_export_filename utility."""

import re
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ImportValidationError, ProfileNotFoundError
from app.models.settings_profile import SettingsProfile
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService, generate_export_filename


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
def service(async_session: AsyncSession) -> ProfileService:
    """Create a ProfileService with the test session."""
    return ProfileService(async_session)


@pytest.fixture
def repo(async_session: AsyncSession) -> ProfileRepository:
    """Create a ProfileRepository for test setup."""
    return ProfileRepository(async_session)


def _make_profile(
    name: str = "Test Profile",
    description: str = "A test profile",
    is_default: bool = False,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> SettingsProfile:
    """Helper to create a SettingsProfile instance."""
    now = datetime.now(timezone.utc).isoformat()
    return SettingsProfile(
        name=name,
        description=description,
        is_default=is_default,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


class TestExportProfile:
    """Tests for ProfileService.export_profile()."""

    async def test_export_returns_correct_structure(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Export returns correct JSON structure with version, exported_at, profile, settings."""
        profile = await repo.create(
            _make_profile(name="Export Test", description="desc for export", is_default=True)
        )
        await async_session.commit()

        result = await service.export_profile(profile.id)

        assert result["version"] == "1.0"
        assert "exported_at" in result
        # exported_at should be a valid ISO datetime
        datetime.fromisoformat(result["exported_at"])

        assert "profile" in result
        assert result["profile"]["name"] == "Export Test"
        assert result["profile"]["description"] == "desc for export"
        assert result["profile"]["is_default"] is True
        assert "created_at" in result["profile"]
        assert "updated_at" in result["profile"]

        assert "settings" in result
        assert "document_type_configs" in result["settings"]
        assert "folder_configs" in result["settings"]
        assert "template_mappings" in result["settings"]
        assert isinstance(result["settings"]["document_type_configs"], list)
        assert isinstance(result["settings"]["folder_configs"], list)
        assert isinstance(result["settings"]["template_mappings"], list)

    async def test_export_nonexistent_profile_raises_404(self, service: ProfileService):
        """Export of nonexistent profile raises ProfileNotFoundError."""
        with pytest.raises(ProfileNotFoundError):
            await service.export_profile(999)

    async def test_export_preserves_profile_data(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Export preserves all profile fields accurately."""
        profile = await repo.create(
            _make_profile(
                name="데이터 보존 테스트",
                description="한글 설명",
                is_default=False,
                created_at="2024-06-01T10:00:00+00:00",
                updated_at="2024-06-15T12:30:00+00:00",
            )
        )
        await async_session.commit()

        result = await service.export_profile(profile.id)

        assert result["profile"]["name"] == "데이터 보존 테스트"
        assert result["profile"]["description"] == "한글 설명"
        assert result["profile"]["is_default"] is False
        assert result["profile"]["created_at"] == "2024-06-01T10:00:00+00:00"
        assert result["profile"]["updated_at"] == "2024-06-15T12:30:00+00:00"


class TestImportProfile:
    """Tests for ProfileService.import_profile()."""

    async def test_import_creates_profile_with_correct_fields(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Import creates profile with correct name and description."""
        data = {
            "version": "1.0",
            "profile": {
                "name": "Imported Profile",
                "description": "Imported description",
                "is_default": False,
            },
        }

        result = await service.import_profile(data)

        assert result.name == "Imported Profile"
        assert result.description == "Imported description"
        assert result.is_default is False
        assert result.id is not None
        # Timestamps should be set to now (not original)
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_import_rejects_file_over_10mb(self, service: ProfileService):
        """Import rejects file > 10MB."""
        data = {"profile": {"name": "Large File"}}
        file_size = 10 * 1024 * 1024 + 1  # 10MB + 1 byte

        with pytest.raises(ImportValidationError) as exc_info:
            await service.import_profile(data, file_size_bytes=file_size)

        assert "10MB" in str(exc_info.value)

    async def test_import_rejects_missing_name_field(self, service: ProfileService):
        """Import rejects missing 'name' field."""
        data = {"profile": {"description": "No name here"}}

        with pytest.raises(ImportValidationError) as exc_info:
            await service.import_profile(data)

        assert "프로필명" in str(exc_info.value)

    async def test_import_rejects_invalid_json_structure_no_profile_key(
        self, service: ProfileService
    ):
        """Import rejects invalid JSON structure (missing 'profile' key)."""
        data = {"name": "Wrong structure"}

        with pytest.raises(ImportValidationError) as exc_info:
            await service.import_profile(data)

        assert "profile" in str(exc_info.value).lower()

    async def test_import_rejects_non_dict_input(self, service: ProfileService):
        """Import rejects non-dict input."""
        with pytest.raises(ImportValidationError):
            await service.import_profile("not a dict")  # type: ignore

    async def test_import_sets_is_default_false_when_default_exists(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Import sets is_default=False when default already exists."""
        # Create existing default profile
        await repo.create(_make_profile(name="Existing Default", is_default=True))
        await async_session.commit()

        data = {
            "profile": {
                "name": "Imported With Default",
                "description": "",
                "is_default": True,
            },
        }

        result = await service.import_profile(data)

        assert result.is_default is False

    async def test_import_allows_is_default_true_when_no_default_exists(
        self, service: ProfileService
    ):
        """Import allows is_default=True when no default profile exists."""
        data = {
            "profile": {
                "name": "New Default",
                "description": "",
                "is_default": True,
            },
        }

        result = await service.import_profile(data)

        assert result.is_default is True

    async def test_import_resets_timestamps(
        self, service: ProfileService
    ):
        """Import resets created_at and updated_at to current time."""
        data = {
            "profile": {
                "name": "Timestamp Test",
                "description": "",
                "is_default": False,
                "created_at": "2020-01-01T00:00:00+00:00",
                "updated_at": "2020-01-01T00:00:00+00:00",
            },
        }

        before = datetime.now(timezone.utc).isoformat()
        result = await service.import_profile(data)

        # Timestamps should be recent, not the old ones from the import data
        assert result.created_at >= before
        assert result.updated_at >= before

    async def test_import_rejects_empty_name(self, service: ProfileService):
        """Import rejects empty string name."""
        data = {"profile": {"name": ""}}

        with pytest.raises(ImportValidationError):
            await service.import_profile(data)

    async def test_import_rejects_whitespace_only_name(self, service: ProfileService):
        """Import rejects whitespace-only name."""
        data = {"profile": {"name": "   "}}

        with pytest.raises(ImportValidationError):
            await service.import_profile(data)

    async def test_import_exactly_10mb_is_accepted(self, service: ProfileService):
        """Import accepts file of exactly 10MB."""
        data = {"profile": {"name": "Exact 10MB"}}
        file_size = 10 * 1024 * 1024  # exactly 10MB

        result = await service.import_profile(data, file_size_bytes=file_size)
        assert result.name == "Exact 10MB"


class TestGenerateExportFilename:
    """Tests for generate_export_filename utility."""

    def test_replaces_all_forbidden_characters(self):
        """All forbidden chars are replaced with underscore."""
        name_with_forbidden = 'a\\b/c:d*e?f"g<h>i|j'
        result = generate_export_filename(name_with_forbidden)

        # No forbidden chars should remain in the result
        forbidden_chars = set('\\/:*?"<>|')
        for char in forbidden_chars:
            assert char not in result

    def test_format_matches_pattern(self):
        """Filename format matches 'profile_{name}_{YYYYMMDD}.json'."""
        result = generate_export_filename("TestProfile")

        pattern = r"^profile_TestProfile_\d{8}\.json$"
        assert re.match(pattern, result) is not None

    def test_date_is_current(self):
        """Date in filename matches current UTC date."""
        result = generate_export_filename("MyProfile")
        today = datetime.now(timezone.utc).strftime("%Y%m%d")

        assert today in result

    def test_clean_name_unchanged(self):
        """Profile name without forbidden chars passes through unchanged."""
        result = generate_export_filename("Clean Name")
        assert "Clean Name" in result

    def test_korean_name_preserved(self):
        """Korean characters are preserved in filename."""
        result = generate_export_filename("현장A 프로필")
        assert "현장A 프로필" in result

    def test_multiple_consecutive_forbidden_chars(self):
        """Multiple consecutive forbidden chars each become underscore."""
        result = generate_export_filename("a**b//c")
        # Each forbidden char should be individually replaced
        assert "a__b__c" in result

    def test_single_forbidden_char_replacement(self):
        """Each forbidden char is individually replaced."""
        for char in '\\/:*?"<>|':
            result = generate_export_filename(f"test{char}name")
            assert char not in result
            assert "test_name" in result
