"""FastAPI exception handlers for the profile management system.

Registers global exception handlers that convert custom exceptions
into structured JSON error responses with appropriate HTTP status codes.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    CopyNameExhaustedError,
    ImportValidationError,
    LastProfileDeleteError,
    ProfileNameDuplicateError,
    ProfileNotFoundError,
)

logger = logging.getLogger(__name__)


class ErrorCodes:
    """Machine-readable error codes for API responses."""

    PROFILE_NAME_REQUIRED = "PROFILE_NAME_REQUIRED"
    PROFILE_NAME_TOO_LONG = "PROFILE_NAME_TOO_LONG"
    PROFILE_DESC_TOO_LONG = "PROFILE_DESC_TOO_LONG"
    PROFILE_NAME_DUPLICATE = "PROFILE_NAME_DUPLICATE"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_LAST_DELETE = "PROFILE_LAST_DELETE"
    IMPORT_INVALID_JSON = "IMPORT_INVALID_JSON"
    IMPORT_MISSING_FIELD = "IMPORT_MISSING_FIELD"
    IMPORT_FILE_TOO_LARGE = "IMPORT_FILE_TOO_LARGE"
    EXPORT_SAVE_FAILED = "EXPORT_SAVE_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    COPY_NAME_EXHAUSTED = "COPY_NAME_EXHAUSTED"


def _determine_import_error_code(reason: str) -> str:
    """Determine the specific error code from an ImportValidationError reason."""
    reason_lower = reason.lower()
    if "json" in reason_lower or "파싱" in reason_lower or "parse" in reason_lower:
        return ErrorCodes.IMPORT_INVALID_JSON
    if "필수" in reason_lower or "누락" in reason_lower or "missing" in reason_lower or "name" in reason_lower:
        return ErrorCodes.IMPORT_MISSING_FIELD
    if "크기" in reason_lower or "size" in reason_lower or "10mb" in reason_lower or "too large" in reason_lower:
        return ErrorCodes.IMPORT_FILE_TOO_LARGE
    return ErrorCodes.IMPORT_INVALID_JSON


def _determine_import_message(error_code: str) -> str:
    """Return a user-facing message for import error codes."""
    messages = {
        ErrorCodes.IMPORT_INVALID_JSON: "유효하지 않은 JSON 파일입니다.",
        ErrorCodes.IMPORT_MISSING_FIELD: "필수 항목(프로필명)이 누락되었습니다.",
        ErrorCodes.IMPORT_FILE_TOO_LARGE: "파일 크기가 10MB를 초과합니다.",
    }
    return messages.get(error_code, "가져오기 유효성 검증에 실패했습니다.")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with the FastAPI application."""

    @app.exception_handler(ProfileNotFoundError)
    async def profile_not_found_handler(
        request: Request, exc: ProfileNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": ErrorCodes.PROFILE_NOT_FOUND,
                "message": "해당 프로필을 찾을 수 없습니다.",
                "detail": str(exc),
                "field": None,
            },
        )

    @app.exception_handler(ProfileNameDuplicateError)
    async def profile_name_duplicate_handler(
        request: Request, exc: ProfileNameDuplicateError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error_code": ErrorCodes.PROFILE_NAME_DUPLICATE,
                "message": "동일한 이름의 프로필이 이미 존재합니다.",
                "detail": str(exc),
                "field": "name",
            },
        )

    @app.exception_handler(LastProfileDeleteError)
    async def last_profile_delete_handler(
        request: Request, exc: LastProfileDeleteError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": ErrorCodes.PROFILE_LAST_DELETE,
                "message": "최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다.",
                "detail": str(exc),
                "field": None,
            },
        )

    @app.exception_handler(ImportValidationError)
    async def import_validation_handler(
        request: Request, exc: ImportValidationError
    ) -> JSONResponse:
        error_code = _determine_import_error_code(exc.reason)
        message = _determine_import_message(error_code)
        return JSONResponse(
            status_code=400,
            content={
                "error_code": error_code,
                "message": message,
                "detail": exc.reason,
                "field": None,
            },
        )

    @app.exception_handler(CopyNameExhaustedError)
    async def copy_name_exhausted_handler(
        request: Request, exc: CopyNameExhaustedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error_code": ErrorCodes.COPY_NAME_EXHAUSTED,
                "message": "복사본 이름을 생성할 수 없습니다. 기존 복사본 이름을 정리해 주세요.",
                "detail": str(exc),
                "field": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        # Extract first error for the primary response
        if errors:
            first_error = errors[0]
            loc = first_error.get("loc", [])
            msg = first_error.get("msg", "")
            field_name = str(loc[-1]) if loc else None

            # Determine error code from validation message and field
            error_code = _determine_validation_error_code(field_name, msg)
            message = _determine_validation_message(error_code)
        else:
            error_code = ErrorCodes.PROFILE_NAME_REQUIRED
            message = "요청 데이터가 유효하지 않습니다."
            field_name = None

        return JSONResponse(
            status_code=422,
            content={
                "error_code": error_code,
                "message": message,
                "detail": str(errors),
                "field": field_name,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": ErrorCodes.DATABASE_ERROR,
                "message": "서버 내부 오류가 발생했습니다.",
                "detail": str(exc) if str(exc) else None,
                "field": None,
            },
        )


def _determine_validation_error_code(field_name: str | None, msg: str) -> str:
    """Determine error code from Pydantic validation error info."""
    msg_lower = msg.lower()

    if field_name == "name":
        if "필수" in msg_lower or "required" in msg_lower or "missing" in msg_lower:
            return ErrorCodes.PROFILE_NAME_REQUIRED
        if "50" in msg or "초과" in msg_lower or "too_long" in msg_lower or "max" in msg_lower:
            return ErrorCodes.PROFILE_NAME_TOO_LONG
        # Default for name field validation errors
        return ErrorCodes.PROFILE_NAME_REQUIRED

    if field_name == "description":
        if "200" in msg or "초과" in msg_lower or "too_long" in msg_lower or "max" in msg_lower:
            return ErrorCodes.PROFILE_DESC_TOO_LONG
        return ErrorCodes.PROFILE_DESC_TOO_LONG

    # Fallback for body-level or unknown field errors
    if "name" in msg_lower:
        return ErrorCodes.PROFILE_NAME_REQUIRED

    return ErrorCodes.PROFILE_NAME_REQUIRED


def _determine_validation_message(error_code: str) -> str:
    """Return user-facing message for validation error codes."""
    messages = {
        ErrorCodes.PROFILE_NAME_REQUIRED: "프로필명은 필수 입력값입니다.",
        ErrorCodes.PROFILE_NAME_TOO_LONG: "프로필명은 50자를 초과할 수 없습니다.",
        ErrorCodes.PROFILE_DESC_TOO_LONG: "설명은 200자를 초과할 수 없습니다.",
    }
    return messages.get(error_code, "요청 데이터가 유효하지 않습니다.")
