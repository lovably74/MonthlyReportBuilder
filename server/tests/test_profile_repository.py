"""Tests for ProfileRepository using an in-memory SQLite database."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.settings_profile import SettingsProfile
from app.repositories.profile_repository import ProfileRepository


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


class TestCreate:
    """Tests for ProfileRepository.create()."""

    async def test_create_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = _make_profile(name="My Profile")
        created = await repo.create(profile)
        await async_session.commit()

        assert created.id is not None
        assert created.name == "My Profile"
        assert created.description == "A test profile"
        assert created.is_default is False

    async def test_create_assigns_auto_id(self, repo: ProfileRepository, async_session: AsyncSession):
        p1 = await repo.create(_make_profile(name="Profile 1"))
        p2 = await repo.create(_make_profile(name="Profile 2"))
        await async_session.commit()

        assert p1.id != p2.id
        assert p2.id > p1.id


class TestGetById:
    """Tests for ProfileRepository.get_by_id()."""

    async def test_get_existing_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = await repo.create(_make_profile(name="Findable"))
        await async_session.commit()

        found = await repo.get_by_id(profile.id)
        assert found is not None
        assert found.name == "Findable"

    async def test_get_nonexistent_profile(self, repo: ProfileRepository):
        found = await repo.get_by_id(999)
        assert found is None


class TestGetByName:
    """Tests for ProfileRepository.get_by_name() - case insensitive."""

    async def test_exact_match(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="TestName"))
        await async_session.commit()

        found = await repo.get_by_name("TestName")
        assert found is not None
        assert found.name == "TestName"

    async def test_case_insensitive_match(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="MyProfile"))
        await async_session.commit()

        found = await repo.get_by_name("myprofile")
        assert found is not None
        assert found.name == "MyProfile"

    async def test_case_insensitive_uppercase(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="hello world"))
        await async_session.commit()

        found = await repo.get_by_name("HELLO WORLD")
        assert found is not None
        assert found.name == "hello world"

    async def test_no_match(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Exists"))
        await async_session.commit()

        found = await repo.get_by_name("DoesNotExist")
        assert found is None


class TestGetDefault:
    """Tests for ProfileRepository.get_default()."""

    async def test_returns_default_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Normal", is_default=False))
        await repo.create(_make_profile(name="Default One", is_default=True))
        await async_session.commit()

        default = await repo.get_default()
        assert default is not None
        assert default.name == "Default One"
        assert default.is_default is True

    async def test_returns_none_when_no_default(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Non-default", is_default=False))
        await async_session.commit()

        default = await repo.get_default()
        assert default is None


class TestListAll:
    """Tests for ProfileRepository.list_all()."""

    async def test_empty_list(self, repo: ProfileRepository):
        profiles = await repo.list_all()
        assert profiles == []

    async def test_returns_all_profiles(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="A", updated_at="2024-01-01T00:00:00"))
        await repo.create(_make_profile(name="B", updated_at="2024-01-02T00:00:00"))
        await repo.create(_make_profile(name="C", updated_at="2024-01-03T00:00:00"))
        await async_session.commit()

        profiles = await repo.list_all()
        assert len(profiles) == 3

    async def test_ordered_by_updated_at_desc(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Old", updated_at="2024-01-01T00:00:00"))
        await repo.create(_make_profile(name="Mid", updated_at="2024-01-02T00:00:00"))
        await repo.create(_make_profile(name="New", updated_at="2024-01-03T00:00:00"))
        await async_session.commit()

        profiles = await repo.list_all()
        assert profiles[0].name == "New"
        assert profiles[1].name == "Mid"
        assert profiles[2].name == "Old"


class TestUpdate:
    """Tests for ProfileRepository.update()."""

    async def test_update_name(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = await repo.create(_make_profile(name="Original"))
        await async_session.commit()

        profile.name = "Updated"
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        updated = await repo.update(profile)
        await async_session.commit()

        assert updated.name == "Updated"

        fetched = await repo.get_by_id(profile.id)
        assert fetched.name == "Updated"

    async def test_update_description(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = await repo.create(_make_profile(name="Profile", description="Old desc"))
        await async_session.commit()

        profile.description = "New description"
        await repo.update(profile)
        await async_session.commit()

        fetched = await repo.get_by_id(profile.id)
        assert fetched.description == "New description"

    async def test_update_is_default(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = await repo.create(_make_profile(name="Profile", is_default=False))
        await async_session.commit()

        profile.is_default = True
        await repo.update(profile)
        await async_session.commit()

        fetched = await repo.get_by_id(profile.id)
        assert fetched.is_default is True


class TestDelete:
    """Tests for ProfileRepository.delete()."""

    async def test_delete_existing_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        profile = await repo.create(_make_profile(name="To Delete"))
        await async_session.commit()

        await repo.delete(profile.id)
        await async_session.commit()

        found = await repo.get_by_id(profile.id)
        assert found is None

    async def test_delete_nonexistent_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        # Should not raise when profile doesn't exist
        await repo.delete(999)
        await async_session.commit()

    async def test_delete_reduces_count(self, repo: ProfileRepository, async_session: AsyncSession):
        p1 = await repo.create(_make_profile(name="P1"))
        await repo.create(_make_profile(name="P2"))
        await async_session.commit()

        assert await repo.count() == 2
        await repo.delete(p1.id)
        await async_session.commit()
        assert await repo.count() == 1


class TestCount:
    """Tests for ProfileRepository.count()."""

    async def test_count_empty(self, repo: ProfileRepository):
        assert await repo.count() == 0

    async def test_count_after_inserts(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="A"))
        await repo.create(_make_profile(name="B"))
        await repo.create(_make_profile(name="C"))
        await async_session.commit()

        assert await repo.count() == 3


class TestGetLatestUpdated:
    """Tests for ProfileRepository.get_latest_updated()."""

    async def test_returns_most_recently_updated(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Old", updated_at="2024-01-01T00:00:00"))
        await repo.create(_make_profile(name="Newest", updated_at="2024-06-15T12:00:00"))
        await repo.create(_make_profile(name="Mid", updated_at="2024-03-01T00:00:00"))
        await async_session.commit()

        latest = await repo.get_latest_updated()
        assert latest is not None
        assert latest.name == "Newest"

    async def test_returns_none_when_empty(self, repo: ProfileRepository):
        latest = await repo.get_latest_updated()
        assert latest is None

    async def test_single_profile(self, repo: ProfileRepository, async_session: AsyncSession):
        await repo.create(_make_profile(name="Only One", updated_at="2024-01-01T00:00:00"))
        await async_session.commit()

        latest = await repo.get_latest_updated()
        assert latest is not None
        assert latest.name == "Only One"
