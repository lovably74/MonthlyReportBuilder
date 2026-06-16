"""Server-ID generation and persistence module.

Generates a UUID v4 on first server run and persists it to a local JSON file.
On subsequent runs, loads the existing Server-ID from the file.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Default path for the server_id.json file
from app.core.database import DATA_DIR as _DEFAULT_DATA_DIR
_DEFAULT_SERVER_ID_FILE = _DEFAULT_DATA_DIR / "server_id.json"

# Module-level cache for the Server-ID
_cached_server_id: str | None = None


def _generate_server_id() -> str:
    """Generate a new UUID v4 Server-ID."""
    return str(uuid.uuid4())


def _save_server_id(server_id: str, file_path: Path) -> None:
    """Save the Server-ID to a JSON file.

    Creates the parent directory if it does not exist.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "server_id": server_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_server_id(file_path: Path) -> str | None:
    """Load the Server-ID from a JSON file.

    Returns None if the file does not exist or contains invalid JSON.
    """
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
        server_id = data.get("server_id")
        if not server_id or not isinstance(server_id, str):
            return None
        # Validate that it looks like a valid UUID
        uuid.UUID(server_id, version=4)
        return server_id
    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        return None


def get_server_id(file_path: Path | None = None) -> str:
    """Get the current Server-ID.

    On first call (or if the file is missing/corrupted):
      - Generates a new UUID v4
      - Saves it to server_id.json

    On subsequent calls:
      - Returns the cached Server-ID (or loads from file if cache is empty)

    Args:
        file_path: Optional custom path for the server_id.json file.
                   Defaults to server/data/server_id.json.

    Returns:
        The Server-ID string (UUID v4 format).
    """
    global _cached_server_id

    if file_path is None:
        file_path = _DEFAULT_SERVER_ID_FILE

    # Return cached value if available
    if _cached_server_id is not None:
        return _cached_server_id

    # Try to load from file
    server_id = _load_server_id(file_path)

    if server_id is None:
        # First run or corrupted file: generate new ID
        server_id = _generate_server_id()
        _save_server_id(server_id, file_path)

    _cached_server_id = server_id
    return server_id


def reset_cache() -> None:
    """Reset the in-memory Server-ID cache.

    Primarily used for testing purposes.
    """
    global _cached_server_id
    _cached_server_id = None
