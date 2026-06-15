"""Tests for ProfileService.copy_profile and set_default_profile methods."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ProfileNotFoundError
from app.models.settings_profile import SettingsProfile
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
def service(async_session: AsyncSession) -> ProfileService:
    """Create a ProfileService with the test session."""
    return ProfileService(async_session)


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


async def _create_profile(
    session: AsyncSession,
    name: str = "Test Profile",
    description: str = "A test profile",
    is_default: bool = False,
    updated_at: str | None = None,
) -> SettingsProfile:
    """Helper to create and persist a profile."""
    now = datetime.now(timezone.utc).isoformat()
    profile = SettingsProfile(
        name=name,
        description=description,
        is_default=is_default,
        created_at=now,
        updated_at=updated_at or now,
    )
    session.add(profile)
    await session.flush()
    await session.refresh(profile)
    await session.commit()
    return profile


class TestCopyProfile:
    """Tests for ProfileService.copy_profile()."""

    async def test_copy_creates_profile_with_correct_name(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copy creates a profile with name '원본이름 (복사본)'."""
        original = await _create_profile(async_session, name="현장A")

        copy = await service.copy_profile(original.id)

        assert copy.name == "현장A (복사본)"

    async def test_copy_sets_is_default_false(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copied profile always has is_default=False."""
        original = await _create_profile(
            async_session, name="Default Profile", is_default=True
        )

        copy = await service.copy_profile(original.id)

        assert copy.is_default is False

    async def test_copy_preserves_description(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copied profile inherits the original's description."""
        original = await _create_profile(
            async_session,
            name="프로필X",
            description="상세 설명 텍스트입니다",
        )

        copy = await service.copy_profile(original.id)

        assert copy.description == "상세 설명 텍스트입니다"

    async def test_copy_preserves_empty_description(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copied profile inherits empty description correctly."""
        original = await _create_profile(
            async_session, name="빈설명", description=""
        )

        copy = await service.copy_profile(original.id)

        assert copy.description == ""

    async def test_sequential_copies_generate_numbered_names(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Sequential copies generate '복사본 2', '복사본 3' etc."""
        original = await _create_profile(async_session, name="원본")

        copy1 = await service.copy_profile(original.id)
        assert copy1.name == "원본 (복사본)"

        copy2 = await service.copy_profile(original.id)
        assert copy2.name == "원본 (복사본 2)"

        copy3 = await service.copy_profile(original.id)
        assert copy3.name == "원본 (복사본 3)"

    async def test_copy_nonexistent_profile_raises_404(
        self, service: ProfileService
    ):
        """Copying a non-existent profile raises ProfileNotFoundError."""
        with pytest.raises(ProfileNotFoundError):
            await service.copy_profile(9999)

    async def test_copy_sets_timestamps(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copied profile has new created_at and updated_at timestamps."""
        original = await _create_profile(
            async_session,
            name="타임스탬프",
            updated_at="2020-01-01T00:00:00+00:00",
        )

        before = datetime.now(timezone.utc).isoformat()
        copy = await service.copy_profile(original.id)

        assert copy.created_at >= before
        assert copy.updated_at >= before

    async def test_copy_has_new_id(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Copied profile gets a new unique ID."""
        original = await _create_profile(async_session, name="원본ID")

        copy = await service.copy_profile(original.id)

        assert copy.id is not None
        assert copy.id != original.id


class TestSetDefaultProfile:
    """Tests for ProfileService.set_default_profile()."""

    async def test_set_default_on_non_default_profile(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Setting a non-default profile as default makes it default."""
        await _create_profile(
            async_session, name="기존 기본", is_default=True
        )
        target = await _create_profile(
            async_session, name="새 기본", is_default=False
        )

        result = await service.set_default_profile(target.id)

        assert result.is_default is True
        assert result.name == "새 기본"

    async def test_set_default_unsets_previous_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Setting a new default unsets the previous default profile."""
        old_default = await _create_profile(
            async_session, name="이전 기본", is_default=True
        )
        target = await _create_profile(
            async_session, name="새 기본", is_default=False
        )

        await service.set_default_profile(target.id)

        # Refresh old_default to get latest state
        await async_session.refresh(old_default)
        assert old_default.is_default is False

    async def test_set_default_updates_both_updated_at(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Both old and new default profiles get updated_at refreshed."""
        old_time = "2020-01-01T00:00:00+00:00"
        old_default = await _create_profile(
            async_session, name="Old Default", is_default=True, updated_at=old_time
        )
        target = await _create_profile(
            async_session, name="New Default", is_default=False, updated_at=old_time
        )

        before = datetime.now(timezone.utc).isoformat()
        await service.set_default_profile(target.id)

        await async_session.refresh(old_default)
        await async_session.refresh(target)

        assert old_default.updated_at >= before
        assert target.updated_at >= before

    async def test_set_default_on_nonexistent_profile_raises_404(
        self, service: ProfileService
    ):
        """Setting default on non-existent profile raises ProfileNotFoundError."""
        with pytest.raises(ProfileNotFoundError):
            await service.set_default_profile(9999)

    async def test_set_default_on_already_default_profile(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Setting default on already-default profile still succeeds."""
        profile = await _create_profile(
            async_session, name="Already Default", is_default=True
        )

        result = await service.set_default_profile(profile.id)

        assert result.is_default is True
        assert result.name == "Already Default"

    async def test_set_default_when_no_previous_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Setting default when there is no existing default works correctly."""
        target = await _create_profile(
            async_session, name="First Default", is_default=False
        )

        result = await service.set_default_profile(target.id)

        assert result.is_default is True
