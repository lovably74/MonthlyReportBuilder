"""ProfileService: business logic layer for profile management.

Implements create, update, delete, copy, set_default operations with:
- Name uniqueness validation (case-insensitive)
- Auto-default assignment for first profile
- Timestamp management
- Last-profile deletion prevention
- Default profile delegation on deletion
- Copy name generation with suffix increment
"""

import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CopyNameExhaustedError,
    ImportValidationError,
    LastProfileDeleteError,
    ProfileNameDuplicateError,
    ProfileNotFoundError,
)
from app.models.settings_profile import SettingsProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate

# Maximum import file size: 10MB
MAX_IMPORT_FILE_SIZE = 10 * 1024 * 1024

# Regex pattern for filesystem-forbidden characters
_FORBIDDEN_CHARS_RE = re.compile(r'[\\/:*?"<>|]')


class ProfileService:
    """Service encapsulating profile business logic.

    Receives an AsyncSession to construct the repository and manage transactions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProfileRepository(session)

    # ─── Task 7.1: Create, Update, Delete ───────────────────────────────

    async def create_profile(self, data: ProfileCreate) -> SettingsProfile:
        """Create a new profile.

        Steps:
            1. Check name uniqueness (case-insensitive)
            2. If no profiles exist, auto-set is_default=True
            3. Set created_at and updated_at to current time
            4. Create and return the profile

        Args:
            data: Validated profile creation input.

        Returns:
            The newly created SettingsProfile.

        Raises:
            ProfileNameDuplicateError: If a profile with the same name exists.
        """
        # 1. Check name uniqueness (case-insensitive)
        existing = await self.repo.get_by_name(data.name)
        if existing is not None:
            raise ProfileNameDuplicateError(data.name)

        # 2. Determine if this should be the default profile
        count = await self.repo.count()
        is_default = count == 0

        # 3. Set timestamps
        now = datetime.now(timezone.utc).isoformat()

        # 4. Create the profile
        profile = SettingsProfile(
            name=data.name,
            description=data.description,
            is_default=is_default,
            created_at=now,
            updated_at=now,
        )

        return await self.repo.create(profile)

    async def update_profile(
        self, profile_id: int, data: ProfileUpdate
    ) -> SettingsProfile:
        """Update an existing profile.

        Steps:
            1. Check profile exists (raise 404 if not)
            2. If name changed, check uniqueness (excluding self)
            3. Update fields, set updated_at to now
            4. Return updated profile

        Args:
            profile_id: The ID of the profile to update.
            data: Validated profile update input.

        Returns:
            The updated SettingsProfile.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ProfileNameDuplicateError: If the new name conflicts with another profile.
        """
        # 1. Check profile exists
        profile = await self.repo.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundError(profile_id)

        # 2. If name is being changed, check uniqueness (excluding self)
        if data.name is not None:
            existing = await self.repo.get_by_name(data.name)
            if existing is not None and existing.id != profile_id:
                raise ProfileNameDuplicateError(data.name)
            profile.name = data.name

        # 3. Update description if provided
        if data.description is not None:
            profile.description = data.description

        # 4. Update timestamp
        profile.updated_at = datetime.now(timezone.utc).isoformat()

        return await self.repo.update(profile)

    async def delete_profile(self, profile_id: int) -> None:
        """Delete a profile.

        Steps:
            1. Check profile exists (raise 404 if not)
            2. Check not the last profile (raise 400 if so)
            3. Delete the profile
            4. If was default, assign default to most recently updated remaining profile

        Args:
            profile_id: The ID of the profile to delete.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
            LastProfileDeleteError: If this is the last remaining profile.
        """
        # 1. Check profile exists
        profile = await self.repo.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundError(profile_id)

        # 2. Check not the last profile
        total = await self.repo.count()
        if total <= 1:
            raise LastProfileDeleteError()

        # 3. Remember if it was the default
        was_default = profile.is_default

        # 4. Delete the profile
        await self.repo.delete(profile_id)

        # 5. If was default, assign default to most recently updated remaining profile
        if was_default:
            latest = await self.repo.get_latest_updated()
            if latest is not None:
                latest.is_default = True
                latest.updated_at = datetime.now(timezone.utc).isoformat()
                await self.repo.update(latest)

    # ─── Task 7.4: List, Get ────────────────────────────────────────────

    async def list_profiles(self) -> list[SettingsProfile]:
        """Return all profiles sorted: default first, then by updated_at descending.

        Sorting logic:
        - The default profile (is_default=True) is always the first item
        - Remaining profiles sorted by updated_at descending (newest first)
        - If no profiles exist, return empty list
        """
        all_profiles = await self.repo.list_all()
        if not all_profiles:
            return []

        default_profiles = [p for p in all_profiles if p.is_default]
        non_default_profiles = [p for p in all_profiles if not p.is_default]

        # Sort non-default by updated_at descending
        non_default_profiles.sort(key=lambda p: p.updated_at, reverse=True)

        return default_profiles + non_default_profiles

    async def get_profile(self, profile_id: int) -> SettingsProfile:
        """Retrieve a single profile by ID.

        Args:
            profile_id: The ID of the profile to retrieve.

        Returns:
            The SettingsProfile with the given ID.

        Raises:
            ProfileNotFoundError: If no profile with the given ID exists.
        """
        profile = await self.repo.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundError(profile_id)
        return profile

    # ─── Task 7.2: Copy, Set Default ────────────────────────────────────

    async def copy_profile(self, profile_id: int) -> SettingsProfile:
        """Copy an existing profile.

        1. Get original profile (404 if not found)
        2. Generate copy name: "원본이름 (복사본)", if exists try
           "원본이름 (복사본 2)", up to 99
        3. Create new profile with:
           - name = generated copy name
           - description = original description
           - is_default = False
           - created_at = now, updated_at = now
        4. Return the new profile

        Raises:
            ProfileNotFoundError: If the source profile doesn't exist.
            CopyNameExhaustedError: If all 99 copy name suffixes are taken.
        """
        original = await self.repo.get_by_id(profile_id)
        if original is None:
            raise ProfileNotFoundError(profile_id)

        copy_name = await self._generate_copy_name(original.name)

        now = datetime.now(timezone.utc).isoformat()
        new_profile = SettingsProfile(
            name=copy_name,
            description=original.description,
            is_default=False,
            created_at=now,
            updated_at=now,
        )

        created = await self.repo.create(new_profile)
        await self.session.commit()
        return created

    async def set_default_profile(self, profile_id: int) -> SettingsProfile:
        """Set a profile as the default profile.

        1. Get target profile (404 if not found)
        2. Get current default profile
        3. In single transaction:
           - If current default exists AND is different: set is_default=False,
             update updated_at
           - Set target is_default=True, update updated_at
        4. Return the new default profile

        Raises:
            ProfileNotFoundError: If the target profile doesn't exist.
        """
        target = await self.repo.get_by_id(profile_id)
        if target is None:
            raise ProfileNotFoundError(profile_id)

        current_default = await self.repo.get_default()
        now = datetime.now(timezone.utc).isoformat()

        # Unset current default if it's a different profile
        if current_default is not None and current_default.id != target.id:
            current_default.is_default = False
            current_default.updated_at = now
            await self.repo.update(current_default)

        # Set target as default
        target.is_default = True
        target.updated_at = now
        updated = await self.repo.update(target)

        await self.session.commit()
        return updated

    # ─── Private Helpers ────────────────────────────────────────────────

    async def _generate_copy_name(self, original_name: str) -> str:
        """Generate a unique copy name based on the original profile name.

        Tries "원본이름 (복사본)" first, then "원본이름 (복사본 2)" through
        "원본이름 (복사본 99)".

        Raises:
            CopyNameExhaustedError: If all suffixes 1-99 are taken.
        """
        # First attempt: "원본이름 (복사본)"
        candidate = f"{original_name} (복사본)"
        existing = await self.repo.get_by_name(candidate)
        if existing is None:
            return candidate

        # Subsequent attempts: "원본이름 (복사본 2)" through "원본이름 (복사본 99)"
        for i in range(2, 100):
            candidate = f"{original_name} (복사본 {i})"
            existing = await self.repo.get_by_name(candidate)
            if existing is None:
                return candidate

        raise CopyNameExhaustedError(original_name)

    # ─── Task 7.3: Export / Import ──────────────────────────────────────

    async def export_profile(self, profile_id: int) -> dict:
        """Export a profile as a JSON-compatible dictionary.

        1. Get profile (404 if not found)
        2. Serialize to dict with version, exported_at, profile data, and settings

        Args:
            profile_id: The ID of the profile to export.

        Returns:
            A dict ready for JSON serialization containing profile and settings data.

        Raises:
            ProfileNotFoundError: If the profile doesn't exist.
        """
        profile = await self.repo.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundError(profile_id)

        now = datetime.now(timezone.utc).isoformat()

        return {
            "version": "1.0",
            "exported_at": now,
            "profile": {
                "name": profile.name,
                "description": profile.description,
                "is_default": profile.is_default,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            },
            "settings": {
                "document_type_configs": [],
                "folder_configs": [],
                "template_mappings": [],
            },
        }

    async def import_profile(
        self, data: dict, file_size_bytes: int = 0
    ) -> SettingsProfile:
        """Import a profile from a parsed JSON dictionary.

        1. Validate file size (reject if > 10MB)
        2. Validate JSON structure: must have "profile" key with "name" field
        3. Extract name, description from data["profile"]
        4. If is_default=True in data but default already exists → set is_default=False
        5. Set new created_at and updated_at to now
        6. Create profile (name uniqueness handled by create logic)
        7. Return created profile

        Args:
            data: Parsed JSON dict from the import file.
            file_size_bytes: Size of the original file in bytes.

        Returns:
            The newly created SettingsProfile.

        Raises:
            ImportValidationError: If validation fails (size, structure, fields).
        """
        # 1. Validate file size
        if file_size_bytes > MAX_IMPORT_FILE_SIZE:
            raise ImportValidationError(
                "파일 크기가 10MB를 초과합니다."
            )

        # 2. Validate JSON structure
        if not isinstance(data, dict):
            raise ImportValidationError(
                "유효하지 않은 JSON 형식입니다."
            )

        profile_data = data.get("profile")
        if not isinstance(profile_data, dict):
            raise ImportValidationError(
                "유효하지 않은 JSON 구조입니다. 'profile' 키가 필요합니다."
            )

        # 3. Validate required field: name
        name = profile_data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise ImportValidationError(
                "필수 항목(프로필명)이 누락되었습니다."
            )

        name = name.strip()
        description = profile_data.get("description", "")
        if not isinstance(description, str):
            description = ""

        # 4. Handle is_default
        is_default = profile_data.get("is_default", False)
        if is_default:
            current_default = await self.repo.get_default()
            if current_default is not None:
                is_default = False

        # 5. Set timestamps to now
        now = datetime.now(timezone.utc).isoformat()

        # 6. Create profile
        new_profile = SettingsProfile(
            name=name,
            description=description,
            is_default=bool(is_default),
            created_at=now,
            updated_at=now,
        )

        created = await self.repo.create(new_profile)
        await self.session.commit()
        return created


def generate_export_filename(profile_name: str) -> str:
    """Generate a safe export filename for a profile.

    Replaces filesystem-forbidden characters (\\ / : * ? " < > |) with underscores.
    Format: "profile_{sanitized_name}_{YYYYMMDD}.json"

    Args:
        profile_name: The profile name to sanitize for use in a filename.

    Returns:
        A safe filename string in the format "profile_{name}_{date}.json".
    """
    sanitized = _FORBIDDEN_CHARS_RE.sub("_", profile_name)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"profile_{sanitized}_{date_str}.json"
