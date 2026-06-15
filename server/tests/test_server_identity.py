"""Tests for the Server-ID generation and persistence module."""

import json
import uuid
from pathlib import Path

import pytest

from app.core.server_identity import (
    _load_server_id,
    _save_server_id,
    get_server_id,
    reset_cache,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the module-level cache before each test."""
    reset_cache()
    yield
    reset_cache()


@pytest.fixture
def server_id_file(tmp_path: Path) -> Path:
    """Provide a temporary path for server_id.json."""
    return tmp_path / "data" / "server_id.json"


class TestFirstRun:
    """Tests for first-run behavior (no existing file)."""

    def test_generates_valid_uuid4(self, server_id_file: Path):
        """First run should generate a valid UUID v4."""
        server_id = get_server_id(file_path=server_id_file)

        # Should be a valid UUID v4
        parsed = uuid.UUID(server_id, version=4)
        assert str(parsed) == server_id

    def test_creates_file_on_first_run(self, server_id_file: Path):
        """First run should create the server_id.json file."""
        assert not server_id_file.exists()

        get_server_id(file_path=server_id_file)

        assert server_id_file.exists()

    def test_file_contains_correct_format(self, server_id_file: Path):
        """The saved file should have server_id and created_at fields."""
        server_id = get_server_id(file_path=server_id_file)

        data = json.loads(server_id_file.read_text(encoding="utf-8"))
        assert "server_id" in data
        assert "created_at" in data
        assert data["server_id"] == server_id
        # created_at should be a valid ISO datetime
        assert isinstance(data["created_at"], str)
        assert len(data["created_at"]) > 0

    def test_creates_parent_directories(self, tmp_path: Path):
        """Should create parent directories if they don't exist."""
        deep_path = tmp_path / "a" / "b" / "c" / "server_id.json"
        assert not deep_path.parent.exists()

        get_server_id(file_path=deep_path)

        assert deep_path.exists()


class TestSubsequentRuns:
    """Tests for subsequent calls (file already exists)."""

    def test_returns_same_id_on_subsequent_calls(self, server_id_file: Path):
        """Subsequent calls should return the same Server-ID."""
        first_id = get_server_id(file_path=server_id_file)
        second_id = get_server_id(file_path=server_id_file)

        assert first_id == second_id

    def test_loads_existing_id_from_file(self, server_id_file: Path):
        """Should load existing Server-ID from file after cache reset."""
        original_id = get_server_id(file_path=server_id_file)

        # Reset cache to simulate a new process
        reset_cache()

        loaded_id = get_server_id(file_path=server_id_file)
        assert loaded_id == original_id

    def test_preserves_id_across_cache_resets(self, server_id_file: Path):
        """Server-ID should persist across multiple cache resets."""
        original_id = get_server_id(file_path=server_id_file)

        for _ in range(5):
            reset_cache()
            assert get_server_id(file_path=server_id_file) == original_id


class TestCorruptedFile:
    """Tests for corrupted file handling."""

    def test_regenerates_on_invalid_json(self, server_id_file: Path):
        """Corrupted JSON should trigger regeneration."""
        server_id_file.parent.mkdir(parents=True, exist_ok=True)
        server_id_file.write_text("not valid json {{{", encoding="utf-8")

        server_id = get_server_id(file_path=server_id_file)

        # Should still produce a valid UUID v4
        parsed = uuid.UUID(server_id, version=4)
        assert str(parsed) == server_id

    def test_regenerates_on_missing_server_id_field(self, server_id_file: Path):
        """JSON without server_id field should trigger regeneration."""
        server_id_file.parent.mkdir(parents=True, exist_ok=True)
        server_id_file.write_text(
            json.dumps({"created_at": "2024-01-01T00:00:00+00:00"}),
            encoding="utf-8",
        )

        server_id = get_server_id(file_path=server_id_file)

        parsed = uuid.UUID(server_id, version=4)
        assert str(parsed) == server_id

    def test_regenerates_on_invalid_uuid_format(self, server_id_file: Path):
        """server_id field with invalid UUID should trigger regeneration."""
        server_id_file.parent.mkdir(parents=True, exist_ok=True)
        server_id_file.write_text(
            json.dumps({
                "server_id": "not-a-valid-uuid",
                "created_at": "2024-01-01T00:00:00+00:00",
            }),
            encoding="utf-8",
        )

        server_id = get_server_id(file_path=server_id_file)

        parsed = uuid.UUID(server_id, version=4)
        assert str(parsed) == server_id

    def test_regenerates_on_empty_server_id(self, server_id_file: Path):
        """Empty server_id field should trigger regeneration."""
        server_id_file.parent.mkdir(parents=True, exist_ok=True)
        server_id_file.write_text(
            json.dumps({
                "server_id": "",
                "created_at": "2024-01-01T00:00:00+00:00",
            }),
            encoding="utf-8",
        )

        server_id = get_server_id(file_path=server_id_file)

        parsed = uuid.UUID(server_id, version=4)
        assert str(parsed) == server_id

    def test_overwrites_corrupted_file(self, server_id_file: Path):
        """After regeneration, the file should contain the new valid ID."""
        server_id_file.parent.mkdir(parents=True, exist_ok=True)
        server_id_file.write_text("corrupted content", encoding="utf-8")

        server_id = get_server_id(file_path=server_id_file)

        # File should now have valid content
        data = json.loads(server_id_file.read_text(encoding="utf-8"))
        assert data["server_id"] == server_id


class TestLoadAndSaveHelpers:
    """Tests for internal helper functions."""

    def test_load_returns_none_for_nonexistent_file(self, tmp_path: Path):
        """_load_server_id should return None if file doesn't exist."""
        result = _load_server_id(tmp_path / "nonexistent.json")
        assert result is None

    def test_save_creates_file(self, server_id_file: Path):
        """_save_server_id should create the file with proper content."""
        test_id = str(uuid.uuid4())
        _save_server_id(test_id, server_id_file)

        assert server_id_file.exists()
        data = json.loads(server_id_file.read_text(encoding="utf-8"))
        assert data["server_id"] == test_id
        assert "created_at" in data
