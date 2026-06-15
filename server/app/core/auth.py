"""Server-ID token authentication middleware.

Provides a FastAPI dependency that verifies the X-Server-ID header
against the server's own Server-ID. All /api/v1/ routes should use
this dependency to ensure only authorized clients can access the API.
"""

from fastapi import Header, HTTPException, status

from app.core.server_identity import get_server_id


async def verify_server_id(
    x_server_id: str | None = Header(default=None),
) -> None:
    """FastAPI dependency to verify the X-Server-ID request header.

    Extracts the X-Server-ID header from the incoming request and compares
    it against the server's own Server-ID (UUID v4).

    Args:
        x_server_id: The X-Server-ID header value from the request.

    Raises:
        HTTPException: 401 Unauthorized if the header is missing or
            does not match the server's Server-ID.
    """
    if x_server_id is None or x_server_id != get_server_id():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Server-ID token",
        )
