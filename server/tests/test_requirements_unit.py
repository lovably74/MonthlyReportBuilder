"""Consolidated unit tests for specific requirement validation.

Each test is explicitly tagged with the requirement it validates.
Uses in-memory SQLite for isolation.

Requirements covered:
- Req 1.6: 첫 번째 프로필 생성 시 자동 기본 지정
- Req 2.5: 존재하지 않는 프로필 수정 시 404 반환
- Req 4.5: 마지막 프로필 삭제 방지
- Req 7.7: 기본 프로필 존재 시 is_default=true 가져오기 → false 처리
- Req 7.8: 10MB 초과 파일 거부
- Req 8.5: 빈 목록 조회 시 빈 배열 반환
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import (
    ImportValidationError,
    LastProfileDeleteError,
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
def service(async_session: AsyncSession) -> ProfileService:
    """Create a ProfileService with the test session."""
    return ProfileService(async_session)


@pytest.fixture
def repo(async_session: AsyncSession) -> ProfileRepository:
    """Create a ProfileRepository for test setup."""
    return ProfileRepository(async_session)


# ─── Requirement 1.6: 첫 번째 프로필 생성 시 자동 기본 지정 ────────────────────


class TestReq1_6_FirstProfileAutoDefault:
    """Validates: Requirement 1.6

    WHEN 시스템에 프로필이 하나도 없는 상태에서 첫 번째 프로필이 생성되면,
    THE Profile_Manager SHALL 해당 프로필을 Default_Profile로 자동 지정한다.
    """

    async def test_first_profile_becomes_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 1.6: 시스템에 프로필이 없을 때 첫 프로필 생성 시 is_default=True."""
        data = ProfileCreate(name="첫 번째 프로필", description="설명")
        profile = await service.create_profile(data)
        await async_session.commit()

        assert profile.is_default is True

    async def test_second_profile_is_not_default(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 1.6: 이미 프로필이 존재하면 새 프로필은 is_default=False."""
        await service.create_profile(ProfileCreate(name="First"))
        await async_session.commit()

        second = await service.create_profile(ProfileCreate(name="Second"))
        await async_session.commit()

        assert second.is_default is False

    async def test_first_profile_default_after_all_deleted_and_recreated(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 1.6: 모든 프로필 삭제 후 다시 첫 프로필 생성 시 자동 기본 지정.

        Note: 마지막 프로필 삭제는 방지되므로, repo를 직접 비워서 테스트.
        """
        # Create two profiles, then delete one via service to leave one
        first = await service.create_profile(ProfileCreate(name="A"))
        await async_session.commit()
        second = await service.create_profile(ProfileCreate(name="B"))
        await async_session.commit()

        # Delete second (non-default) is allowed
        await service.delete_profile(second.id)
        await async_session.commit()

        # Now forcibly clear for this edge case test
        repo = ProfileRepository(async_session)
        await repo.delete(first.id)
        await async_session.commit()

        # Create a new first profile in empty system
        new_first = await service.create_profile(ProfileCreate(name="새 프로필"))
        await async_session.commit()

        assert new_first.is_default is True


# ─── Requirement 2.5: 존재하지 않는 프로필 수정 시 404 반환 ───────────────────


class TestReq2_5_UpdateNonexistentProfile404:
    """Validates: Requirement 2.5

    IF 사용자가 존재하지 않는 Profile에 대해 수정을 요청하면,
    THEN THE Profile_Manager SHALL 해당 프로필을 찾을 수 없음을 나타내는
    오류 메시지를 표시하고 어떠한 데이터도 변경하지 않는다.
    """

    async def test_update_nonexistent_profile_raises_not_found(
        self, service: ProfileService
    ):
        """Req 2.5: 존재하지 않는 profile_id로 수정 시 ProfileNotFoundError 발생."""
        with pytest.raises(ProfileNotFoundError) as exc_info:
            await service.update_profile(99999, ProfileUpdate(name="New Name"))

        assert exc_info.value.profile_id == 99999

    async def test_update_nonexistent_does_not_modify_existing(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 2.5: 존재하지 않는 프로필 수정 시도가 기존 데이터를 변경하지 않음."""
        # Create an existing profile
        existing = await service.create_profile(
            ProfileCreate(name="Existing", description="original")
        )
        await async_session.commit()
        original_updated_at = existing.updated_at

        # Try to update a non-existent profile
        with pytest.raises(ProfileNotFoundError):
            await service.update_profile(99999, ProfileUpdate(name="Hacked"))

        # Verify existing profile is unchanged
        unchanged = await service.get_profile(existing.id)
        assert unchanged.name == "Existing"
        assert unchanged.description == "original"
        assert unchanged.updated_at == original_updated_at


# ─── Requirement 4.5: 마지막 프로필 삭제 방지 ────────────────────────────────


class TestReq4_5_PreventLastProfileDeletion:
    """Validates: Requirement 4.5

    IF 시스템에 프로필이 하나만 존재하는 상태에서 삭제를 요청하면,
    THEN THE Profile_Manager SHALL "최소 1개의 프로필이 필요합니다.
    마지막 프로필은 삭제할 수 없습니다."라는 오류 메시지를 표시한다.
    """

    async def test_delete_last_profile_raises_error(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 4.5: 마지막 프로필 삭제 시 LastProfileDeleteError 발생."""
        profile = await service.create_profile(ProfileCreate(name="Only Profile"))
        await async_session.commit()

        with pytest.raises(LastProfileDeleteError) as exc_info:
            await service.delete_profile(profile.id)

        assert "마지막 프로필" in str(exc_info.value)

    async def test_delete_last_profile_preserves_data(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 4.5: 마지막 프로필 삭제 시도 후 프로필이 여전히 존재."""
        profile = await service.create_profile(ProfileCreate(name="Sole"))
        await async_session.commit()

        with pytest.raises(LastProfileDeleteError):
            await service.delete_profile(profile.id)

        # Profile should still exist
        still_exists = await service.get_profile(profile.id)
        assert still_exists is not None
        assert still_exists.name == "Sole"
        assert still_exists.is_default is True


# ─── Requirement 7.7: 기본 프로필 존재 시 is_default=true 가져오기 → false ────


class TestReq7_7_ImportDefaultFalseWhenDefaultExists:
    """Validates: Requirement 7.7

    IF Import_File의 is_default 값이 true이고 현재 시스템에 기본 프로필이
    이미 존재하면, THEN THE Profile_Manager SHALL 가져온 프로필의
    is_default를 false로 설정하여 기존 기본 프로필을 유지한다.
    """

    async def test_import_with_is_default_true_becomes_false(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 7.7: 기본 프로필 존재 시 가져오기의 is_default=true → false 처리."""
        # Create existing default profile
        await service.create_profile(ProfileCreate(name="기존 기본"))
        await async_session.commit()

        # Import with is_default=True
        import_data = {
            "version": "1.0",
            "profile": {
                "name": "가져온 프로필",
                "description": "imported",
                "is_default": True,
            },
        }

        imported = await service.import_profile(import_data)

        assert imported.is_default is False

    async def test_existing_default_remains_default_after_import(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 7.7: 가져오기 후 기존 기본 프로필의 is_default가 유지."""
        existing_default = await service.create_profile(
            ProfileCreate(name="Default Profile")
        )
        await async_session.commit()

        import_data = {
            "version": "1.0",
            "profile": {
                "name": "Imported",
                "description": "",
                "is_default": True,
            },
        }

        await service.import_profile(import_data)

        # Verify existing default is still default
        refreshed = await service.get_profile(existing_default.id)
        assert refreshed.is_default is True

    async def test_import_is_default_true_allowed_when_no_default(
        self, service: ProfileService
    ):
        """Req 7.7: 기본 프로필이 없을 때 is_default=True 그대로 유지."""
        import_data = {
            "version": "1.0",
            "profile": {
                "name": "New Default",
                "description": "",
                "is_default": True,
            },
        }

        imported = await service.import_profile(import_data)

        assert imported.is_default is True


# ─── Requirement 7.8: 10MB 초과 파일 거부 ─────────────────────────────────────


class TestReq7_8_RejectFilesOver10MB:
    """Validates: Requirement 7.8

    IF Import_File의 크기가 10MB를 초과하면,
    THEN THE Profile_Manager SHALL 파일 크기 초과를 나타내는
    오류 메시지를 표시하고, 프로필을 생성하지 않는다.
    """

    async def test_reject_file_over_10mb(self, service: ProfileService):
        """Req 7.8: 10MB 초과 파일 거부."""
        import_data = {"profile": {"name": "Large File"}}
        file_size = 10 * 1024 * 1024 + 1  # 10MB + 1 byte

        with pytest.raises(ImportValidationError) as exc_info:
            await service.import_profile(import_data, file_size_bytes=file_size)

        assert "10MB" in str(exc_info.value)

    async def test_accept_file_exactly_10mb(self, service: ProfileService):
        """Req 7.8: 정확히 10MB 파일은 허용."""
        import_data = {"profile": {"name": "Exactly 10MB"}}
        file_size = 10 * 1024 * 1024  # exactly 10MB

        result = await service.import_profile(import_data, file_size_bytes=file_size)
        assert result.name == "Exactly 10MB"

    async def test_reject_file_well_over_10mb(self, service: ProfileService):
        """Req 7.8: 크게 초과하는 파일도 거부."""
        import_data = {"profile": {"name": "Very Large"}}
        file_size = 50 * 1024 * 1024  # 50MB

        with pytest.raises(ImportValidationError) as exc_info:
            await service.import_profile(import_data, file_size_bytes=file_size)

        assert "10MB" in str(exc_info.value)

    async def test_no_profile_created_when_file_too_large(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 7.8: 파일 크기 초과 시 프로필이 생성되지 않음."""
        import_data = {"profile": {"name": "Should Not Exist"}}
        file_size = 10 * 1024 * 1024 + 100

        with pytest.raises(ImportValidationError):
            await service.import_profile(import_data, file_size_bytes=file_size)

        # Verify nothing was created
        profiles = await service.list_profiles()
        assert len(profiles) == 0


# ─── Requirement 8.5: 빈 목록 조회 시 빈 배열 반환 ───────────────────────────


class TestReq8_5_EmptyListReturnsEmptyArray:
    """Validates: Requirement 8.5

    IF 등록된 프로필이 없으면,
    THEN THE Profile_Manager SHALL 프로필이 없음을 안내하고
    새 프로필 생성을 유도하는 메시지를 표시한다.

    At the service level, this means returning an empty list.
    """

    async def test_list_empty_returns_empty_list(self, service: ProfileService):
        """Req 8.5: 프로필이 없을 때 빈 리스트 반환."""
        result = await service.list_profiles()

        assert result == []
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_list_empty_after_deletion(
        self, service: ProfileService, async_session: AsyncSession
    ):
        """Req 8.5: 모든 프로필 삭제 후(강제) 빈 리스트 반환.

        Note: 정상적으로는 마지막 프로필 삭제가 방지되지만,
        repo를 직접 사용하여 빈 상태를 시뮬레이션.
        """
        # Create and then force-delete to simulate empty state
        profile = await service.create_profile(ProfileCreate(name="Temp"))
        await async_session.commit()

        repo = ProfileRepository(async_session)
        await repo.delete(profile.id)
        await async_session.commit()

        result = await service.list_profiles()
        assert result == []
