"""Tests for ProfileService business logic."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import (
    LastProfileDeleteError,
    ProfileNameDuplicateError,
    ProfileNotFoundError,
)
from app.models.settings_profile import SettingsProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services.profile_service import ProfileService


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
def repo(async_session: AsyncSession) -> ProfileRepository:
    """Create a ProfileRepository with the test session."""
    return ProfileRepository(async_session)


@pytest.fixture
def service(async_session: AsyncSession) -> ProfileService:
    """Create a ProfileService with the test session."""
    return ProfileService(async_session)


def _make_profile(
    name: str = "Test Profile",
    description: str = "",
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


# ─── Task 7.1: Create, Update, Delete Tests ─────────────────────────────────


class TestCreateProfile:
    """Tests for ProfileService.create_profile()."""

    async def test_create_first_profile_is_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """First profile created should automatically be set as default."""
        data = ProfileCreate(name="First Profile", description="desc")
        profile = await service.create_profile(data)
        await async_session.commit()

        assert profile.id is not None
        assert profile.name == "First Profile"
        assert profile.description == "desc"
        assert profile.is_default is True
        assert profile.created_at is not None
        assert profile.updated_at is not None

    async def test_create_second_profile_not_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Subsequent profiles should not be default."""
        await service.create_profile(ProfileCreate(name="First"))
        await async_session.commit()

        second = await service.create_profile(ProfileCreate(name="Second"))
        await async_session.commit()

        assert second.is_default is False

    async def test_create_rejects_duplicate_name_exact(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Creating with an exact duplicate name should raise error."""
        await service.create_profile(ProfileCreate(name="Duplicate"))
        await async_session.commit()

        with pytest.raises(ProfileNameDuplicateError) as exc_info:
            await service.create_profile(ProfileCreate(name="Duplicate"))

        assert "Duplicate" in str(exc_info.value)

    async def test_create_rejects_duplicate_name_case_insensitive(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Creating with a case-different duplicate name should raise error."""
        await service.create_profile(ProfileCreate(name="MyProfile"))
        await async_session.commit()

        with pytest.raises(ProfileNameDuplicateError):
            await service.create_profile(ProfileCreate(name="myprofile"))

    async def test_create_rejects_duplicate_name_mixed_case(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Creating with mixed-case duplicate should raise error."""
        await service.create_profile(ProfileCreate(name="Hello World"))
        await async_session.commit()

        with pytest.raises(ProfileNameDuplicateError):
            await service.create_profile(ProfileCreate(name="HELLO WORLD"))

    async def test_create_sets_timestamps(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Created profile should have valid ISO 8601 timestamps."""
        before = datetime.now(timezone.utc)
        profile = await service.create_profile(ProfileCreate(name="Timestamped"))
        await async_session.commit()

        created_at = datetime.fromisoformat(profile.created_at)
        updated_at = datetime.fromisoformat(profile.updated_at)

        assert created_at >= before
        assert updated_at >= before
        assert created_at == updated_at


class TestUpdateProfile:
    """Tests for ProfileService.update_profile()."""

    async def test_update_name(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating the name should persist correctly."""
        profile = await service.create_profile(ProfileCreate(name="Original"))
        await async_session.commit()

        updated = await service.update_profile(
            profile.id, ProfileUpdate(name="NewName")
        )
        await async_session.commit()

        assert updated.name == "NewName"

    async def test_update_description(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating the description should persist correctly."""
        profile = await service.create_profile(
            ProfileCreate(name="Prof", description="old")
        )
        await async_session.commit()

        updated = await service.update_profile(
            profile.id, ProfileUpdate(description="new desc")
        )
        await async_session.commit()

        assert updated.description == "new desc"

    async def test_update_sets_updated_at(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating should refresh the updated_at timestamp."""
        profile = await service.create_profile(ProfileCreate(name="Prof"))
        await async_session.commit()
        original_updated_at = profile.updated_at

        updated = await service.update_profile(
            profile.id, ProfileUpdate(description="changed")
        )
        await async_session.commit()

        assert updated.updated_at >= original_updated_at

    async def test_update_rejects_duplicate_name(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating to a name that conflicts with another profile should fail."""
        await service.create_profile(ProfileCreate(name="Existing"))
        profile = await service.create_profile(ProfileCreate(name="ToUpdate"))
        await async_session.commit()

        with pytest.raises(ProfileNameDuplicateError):
            await service.update_profile(
                profile.id, ProfileUpdate(name="Existing")
            )

    async def test_update_rejects_duplicate_name_case_insensitive(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating to a case-insensitive duplicate should fail."""
        await service.create_profile(ProfileCreate(name="TakenName"))
        profile = await service.create_profile(ProfileCreate(name="MyProfile"))
        await async_session.commit()

        with pytest.raises(ProfileNameDuplicateError):
            await service.update_profile(
                profile.id, ProfileUpdate(name="takenname")
            )

    async def test_update_allows_same_name_on_self(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Updating to own current name (same case) should not raise."""
        profile = await service.create_profile(ProfileCreate(name="MyName"))
        await async_session.commit()

        updated = await service.update_profile(
            profile.id, ProfileUpdate(name="MyName")
        )
        await async_session.commit()

        assert updated.name == "MyName"

    async def test_update_nonexistent_profile_raises(
        self, service: ProfileService
    ):
        """Updating a non-existent profile should raise ProfileNotFoundError."""
        with pytest.raises(ProfileNotFoundError) as exc_info:
            await service.update_profile(999, ProfileUpdate(name="Whatever"))

        assert exc_info.value.profile_id == 999


class TestDeleteProfile:
    """Tests for ProfileService.delete_profile()."""

    async def test_delete_nonexistent_raises(self, service: ProfileService):
        """Deleting a non-existent profile should raise ProfileNotFoundError."""
        with pytest.raises(ProfileNotFoundError) as exc_info:
            await service.delete_profile(999)

        assert exc_info.value.profile_id == 999

    async def test_delete_last_profile_raises(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Deleting the last remaining profile should raise LastProfileDeleteError."""
        profile = await service.create_profile(ProfileCreate(name="Only One"))
        await async_session.commit()

        with pytest.raises(LastProfileDeleteError):
            await service.delete_profile(profile.id)

    async def test_delete_non_default_profile(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Deleting a non-default profile should work and leave default unchanged."""
        first = await service.create_profile(ProfileCreate(name="Default"))
        await async_session.commit()

        second = await service.create_profile(ProfileCreate(name="ToDelete"))
        await async_session.commit()

        await service.delete_profile(second.id)
        await async_session.commit()

        # Default should remain unchanged
        repo = service.repo
        remaining = await repo.get_by_id(first.id)
        assert remaining is not None
        assert remaining.is_default is True

        deleted = await repo.get_by_id(second.id)
        assert deleted is None

    async def test_delete_default_reassigns_to_latest_updated(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Deleting a default profile should reassign default to the most recently updated profile."""
        # Create first (auto-default)
        default_profile = await service.create_profile(
            ProfileCreate(name="Default")
        )
        await async_session.commit()

        # Create second and third
        await service.create_profile(ProfileCreate(name="Older"))
        await async_session.commit()

        newest = await service.create_profile(ProfileCreate(name="Newest"))
        await async_session.commit()

        # Update "Newest" to ensure it has the latest updated_at
        newest = await service.update_profile(
            newest.id, ProfileUpdate(description="updated")
        )
        await async_session.commit()

        # Delete the default profile
        await service.delete_profile(default_profile.id)
        await async_session.commit()

        # The most recently updated remaining profile should be the new default
        repo = service.repo
        new_default = await repo.get_default()
        assert new_default is not None
        assert new_default.name == "Newest"
        assert new_default.is_default is True

    async def test_delete_default_with_two_profiles(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Deleting default when only two profiles exist should reassign correctly."""
        first = await service.create_profile(ProfileCreate(name="First"))
        await async_session.commit()

        second = await service.create_profile(ProfileCreate(name="Second"))
        await async_session.commit()

        # Delete the default (first)
        await service.delete_profile(first.id)
        await async_session.commit()

        repo = service.repo
        remaining = await repo.get_by_id(second.id)
        assert remaining is not None
        assert remaining.is_default is True


# ─── Task 7.4: List, Get Tests ───────────────────────────────────────────────


class TestListProfiles:
    """Tests for ProfileService.list_profiles()."""

    async def test_empty_list_returns_empty(self, service: ProfileService):
        """Empty database returns empty list."""
        result = await service.list_profiles()
        assert result == []

    async def test_single_default_profile(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """A single default profile is returned as the only item."""
        await repo.create(_make_profile(name="Default", is_default=True))
        await async_session.commit()

        result = await service.list_profiles()
        assert len(result) == 1
        assert result[0].name == "Default"
        assert result[0].is_default is True

    async def test_default_profile_first(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Default profile is always first regardless of updated_at."""
        await repo.create(
            _make_profile(name="Newer", is_default=False, updated_at="2024-06-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="Default", is_default=True, updated_at="2024-01-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="Oldest", is_default=False, updated_at="2023-01-01T00:00:00")
        )
        await async_session.commit()

        result = await service.list_profiles()
        assert len(result) == 3
        assert result[0].name == "Default"
        assert result[0].is_default is True

    async def test_remaining_sorted_by_updated_at_desc(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Non-default profiles are sorted by updated_at descending (newest first)."""
        await repo.create(
            _make_profile(name="Default", is_default=True, updated_at="2024-01-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="Old", is_default=False, updated_at="2024-02-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="Newest", is_default=False, updated_at="2024-06-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="Mid", is_default=False, updated_at="2024-04-01T00:00:00")
        )
        await async_session.commit()

        result = await service.list_profiles()
        assert len(result) == 4
        # First is default
        assert result[0].name == "Default"
        assert result[0].is_default is True
        # Remaining sorted by updated_at desc
        assert result[1].name == "Newest"
        assert result[2].name == "Mid"
        assert result[3].name == "Old"

    async def test_multiple_profiles_no_default(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Even without a default, profiles are sorted by updated_at descending."""
        await repo.create(
            _make_profile(name="A", is_default=False, updated_at="2024-01-01T00:00:00")
        )
        await repo.create(
            _make_profile(name="B", is_default=False, updated_at="2024-06-01T00:00:00")
        )
        await async_session.commit()

        result = await service.list_profiles()
        assert len(result) == 2
        assert result[0].name == "B"
        assert result[1].name == "A"


class TestGetProfile:
    """Tests for ProfileService.get_profile()."""

    async def test_get_existing_profile(
        self, service: ProfileService, repo: ProfileRepository, async_session: AsyncSession
    ):
        """Returns profile when it exists."""
        profile = await repo.create(_make_profile(name="Existing"))
        await async_session.commit()

        result = await service.get_profile(profile.id)
        assert result.name == "Existing"
        assert result.id == profile.id

    async def test_get_nonexistent_raises_404(self, service: ProfileService):
        """Raises ProfileNotFoundError for nonexistent profile ID."""
        with pytest.raises(ProfileNotFoundError) as exc_info:
            await service.get_profile(9999)
        assert exc_info.value.profile_id == 9999
