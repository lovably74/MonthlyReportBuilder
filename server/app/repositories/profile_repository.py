"""ProfileRepository: data access layer for SettingsProfile CRUD operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_profile import SettingsProfile


class ProfileRepository:
    """Repository providing CRUD methods for SettingsProfile entities.

    All queries use SQLAlchemy async session patterns with the provided session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, profile: SettingsProfile) -> SettingsProfile:
        """Insert a new profile into the database."""
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_by_id(self, profile_id: int) -> SettingsProfile | None:
        """Retrieve a profile by its primary key ID."""
        stmt = select(SettingsProfile).where(SettingsProfile.id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> SettingsProfile | None:
        """Retrieve a profile by name (case-insensitive comparison)."""
        stmt = select(SettingsProfile).where(
            func.lower(SettingsProfile.name) == func.lower(name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self) -> SettingsProfile | None:
        """Retrieve the default profile (is_default=True)."""
        stmt = select(SettingsProfile).where(SettingsProfile.is_default == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[SettingsProfile]:
        """Retrieve all profiles ordered by updated_at descending."""
        stmt = select(SettingsProfile).order_by(SettingsProfile.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, profile: SettingsProfile) -> SettingsProfile:
        """Persist changes to an existing profile."""
        await self.session.merge(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete(self, profile_id: int) -> None:
        """Delete a profile by ID."""
        profile = await self.get_by_id(profile_id)
        if profile:
            await self.session.delete(profile)
            await self.session.flush()

    async def count(self) -> int:
        """Return the total number of profiles."""
        stmt = select(func.count()).select_from(SettingsProfile)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_latest_updated(self) -> SettingsProfile | None:
        """Return the profile with the most recent updated_at value."""
        stmt = (
            select(SettingsProfile)
            .order_by(SettingsProfile.updated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
