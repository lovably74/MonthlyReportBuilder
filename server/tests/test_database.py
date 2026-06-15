"""Tests for SQLAlchemy database setup and SettingsProfile ORM model."""

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, DATABASE_URL, engine, async_session_factory
from app.models.settings_profile import SettingsProfile


@pytest.fixture
async def test_session():
    """Create an in-memory SQLite database for testing."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await test_engine.dispose()


class TestDatabaseConfiguration:
    """Tests for database module configuration."""

    def test_database_url_is_sqlite_aiosqlite(self):
        """DATABASE_URL이 sqlite+aiosqlite 프로토콜을 사용하는지 검증."""
        assert DATABASE_URL.startswith("sqlite+aiosqlite:///")

    def test_database_url_points_to_cm_report_db(self):
        """DATABASE_URL이 cm_report.db 파일을 가리키는지 검증."""
        assert DATABASE_URL.endswith("cm_report.db")

    def test_engine_is_created(self):
        """SQLAlchemy async engine이 정상 생성되었는지 검증."""
        assert engine is not None

    def test_session_factory_is_created(self):
        """async_session_factory가 정상 생성되었는지 검증."""
        assert async_session_factory is not None


class TestSettingsProfileModel:
    """Tests for SettingsProfile ORM model."""

    def test_tablename(self):
        """테이블명이 settings_profile인지 검증."""
        assert SettingsProfile.__tablename__ == "settings_profile"

    def test_columns_exist(self):
        """필수 컬럼들이 모두 정의되어 있는지 검증."""
        columns = {col.name for col in SettingsProfile.__table__.columns}
        expected = {"id", "name", "description", "is_default", "created_at", "updated_at"}
        assert expected == columns

    def test_id_is_primary_key(self):
        """id 컬럼이 primary key인지 검증."""
        col = SettingsProfile.__table__.c.id
        assert col.primary_key is True

    def test_name_is_not_nullable(self):
        """name 컬럼이 NOT NULL인지 검증."""
        col = SettingsProfile.__table__.c.name
        assert col.nullable is False

    def test_name_is_unique(self):
        """name 컬럼이 UNIQUE인지 검증."""
        col = SettingsProfile.__table__.c.name
        assert col.unique is True

    def test_is_default_has_default_false(self):
        """is_default 컬럼의 기본값이 False인지 검증."""
        col = SettingsProfile.__table__.c.is_default
        assert col.default.arg is False

    def test_description_has_default_empty_string(self):
        """description 컬럼의 기본값이 빈 문자열인지 검증."""
        col = SettingsProfile.__table__.c.description
        assert col.default.arg == ""

    @pytest.mark.asyncio
    async def test_create_and_read_profile(self, test_session: AsyncSession):
        """프로필 생성 후 조회 시 데이터가 일치하는지 검증."""
        now = datetime.now(timezone.utc).isoformat()
        profile = SettingsProfile(
            name="테스트 프로필",
            description="설명입니다",
            is_default=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(profile)
        await test_session.commit()

        result = await test_session.get(SettingsProfile, profile.id)
        assert result is not None
        assert result.name == "테스트 프로필"
        assert result.description == "설명입니다"
        assert result.is_default is True
        assert result.created_at == now
        assert result.updated_at == now

    @pytest.mark.asyncio
    async def test_unique_name_constraint(self, test_session: AsyncSession):
        """동일한 이름으로 두 번째 프로필 생성 시 IntegrityError 발생 검증."""
        from sqlalchemy.exc import IntegrityError

        now = datetime.now(timezone.utc).isoformat()
        profile1 = SettingsProfile(
            name="중복이름",
            description="",
            is_default=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(profile1)
        await test_session.commit()

        profile2 = SettingsProfile(
            name="중복이름",
            description="",
            is_default=False,
            created_at=now,
            updated_at=now,
        )
        test_session.add(profile2)
        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_indexes_created(self, test_session: AsyncSession):
        """테이블에 필수 인덱스가 생성되었는지 검증."""
        def _check_indexes(conn):
            inspector = inspect(conn)
            indexes = inspector.get_indexes("settings_profile")
            index_names = {idx["name"] for idx in indexes}
            return index_names

        async with test_session.bind.connect() as conn:
            index_names = await conn.run_sync(_check_indexes)

        assert "idx_profile_name" in index_names
        assert "idx_profile_is_default" in index_names
        assert "idx_profile_updated_at" in index_names

    def test_repr(self):
        """__repr__ 메서드가 올바르게 동작하는지 검증."""
        profile = SettingsProfile(id=1, name="Test", is_default=True)
        repr_str = repr(profile)
        assert "SettingsProfile" in repr_str
        assert "Test" in repr_str
        assert "is_default=True" in repr_str
