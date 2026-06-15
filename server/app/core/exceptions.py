"""Custom exception classes for the profile management system."""


class ProfileNotFoundError(Exception):
    """Raised when a profile with the given ID does not exist."""

    def __init__(self, profile_id: int) -> None:
        self.profile_id = profile_id
        super().__init__(f"Profile with id={profile_id} not found.")


class ProfileNameDuplicateError(Exception):
    """Raised when a profile name already exists (case-insensitive)."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Profile name '{name}' already exists.")


class LastProfileDeleteError(Exception):
    """Raised when attempting to delete the last remaining profile."""

    def __init__(self) -> None:
        super().__init__(
            "최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다."
        )


class CopyNameExhaustedError(Exception):
    """Raised when copy name generation exhausts all 99 suffixes."""

    def __init__(self, original_name: str) -> None:
        self.original_name = original_name
        super().__init__(
            f"Cannot generate copy name for '{original_name}': all suffixes exhausted."
        )


class ImportValidationError(Exception):
    """Raised when import file validation fails."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Import validation failed: {reason}")
