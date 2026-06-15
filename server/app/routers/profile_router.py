"""Profile management API router.

Provides endpoints for profile CRUD, copy, set default,
export, and import operations.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_server_id
from app.core.database import get_db
from app.core.exceptions import (
    CopyNameExhaustedError,
    ImportValidationError,
    LastProfileDeleteError,
    ProfileNameDuplicateError,
    ProfileNotFoundError,
)
from app.schemas.profile import (
    ErrorResponse,
    ProfileCreate,
    ProfileListResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.profile_service import MAX_IMPORT_FILE_SIZE, ProfileService

router = APIRouter(
    prefix="/api/v1/profiles",
    tags=["profiles"],
    dependencies=[Depends(verify_server_id)],
)


def _get_service(session: AsyncSession = Depends(get_db)) -> ProfileService:
    """Dependency to create a ProfileService instance."""
    return ProfileService(session)


# ─── CRUD Endpoints (Task 8.1) ───────────────────────────────────────────────


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    service: ProfileService = Depends(_get_service),
) -> ProfileListResponse:
    """프로필 목록 조회."""
    profiles = await service.list_profiles()
    return ProfileListResponse(
        profiles=[ProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles),
    )


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileCreate,
    service: ProfileService = Depends(_get_service),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """프로필 생성."""
    try:
        profile = await service.create_profile(data)
        await session.commit()
        return ProfileResponse.model_validate(profile)
    except ProfileNameDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="PROFILE_NAME_DUPLICATE",
                message="동일한 이름의 프로필이 이미 존재합니다.",
                field="name",
            ).model_dump(),
        )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    service: ProfileService = Depends(_get_service),
) -> ProfileResponse:
    """프로필 상세 조회."""
    try:
        profile = await service.get_profile(profile_id)
        return ProfileResponse.model_validate(profile)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    service: ProfileService = Depends(_get_service),
    session: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """프로필 수정."""
    try:
        profile = await service.update_profile(profile_id, data)
        await session.commit()
        return ProfileResponse.model_validate(profile)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )
    except ProfileNameDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="PROFILE_NAME_DUPLICATE",
                message="동일한 이름의 프로필이 이미 존재합니다.",
                field="name",
            ).model_dump(),
        )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    service: ProfileService = Depends(_get_service),
    session: AsyncSession = Depends(get_db),
) -> None:
    """프로필 삭제."""
    try:
        await service.delete_profile(profile_id)
        await session.commit()
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )
    except LastProfileDeleteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="PROFILE_LAST_DELETE",
                message="최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다.",
            ).model_dump(),
        )


# ─── Copy, Set Default, Export, Import Endpoints (Task 8.2) ──────────────────


@router.post(
    "/{profile_id}/copy",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def copy_profile(
    profile_id: int,
    service: ProfileService = Depends(_get_service),
) -> ProfileResponse:
    """프로필 복사."""
    try:
        profile = await service.copy_profile(profile_id)
        return ProfileResponse.model_validate(profile)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )
    except CopyNameExhaustedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="COPY_NAME_EXHAUSTED",
                message="복사본 이름을 생성할 수 없습니다. 기존 복사본이 너무 많습니다.",
            ).model_dump(),
        )


@router.put(
    "/{profile_id}/default",
    response_model=ProfileResponse,
)
async def set_default_profile(
    profile_id: int,
    service: ProfileService = Depends(_get_service),
) -> ProfileResponse:
    """기본 프로필 지정."""
    try:
        profile = await service.set_default_profile(profile_id)
        return ProfileResponse.model_validate(profile)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )


@router.get("/{profile_id}/export")
async def export_profile(
    profile_id: int,
    service: ProfileService = Depends(_get_service),
) -> dict:
    """프로필 내보내기 (JSON 응답)."""
    try:
        export_data = await service.export_profile(profile_id)
        return export_data
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message="해당 프로필을 찾을 수 없습니다.",
            ).model_dump(),
        )


@router.post(
    "/import",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_profile(
    request: Request,
    service: ProfileService = Depends(_get_service),
    content_length: int | None = Header(default=None, alias="content-length"),
) -> ProfileResponse:
    """프로필 가져오기 (JSON 업로드, 10MB 제한).

    Accepts JSON body matching the export format. Validates Content-Length
    against the 10MB limit before parsing.
    """
    # Validate Content-Length header if present
    if content_length is not None and content_length > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="IMPORT_FILE_TOO_LARGE",
                message="파일 크기가 10MB를 초과합니다.",
            ).model_dump(),
        )

    # Read and parse the body
    body = await request.body()
    body_size = len(body)

    # Double check actual body size
    if body_size > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="IMPORT_FILE_TOO_LARGE",
                message="파일 크기가 10MB를 초과합니다.",
            ).model_dump(),
        )

    # Parse JSON
    import json

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="IMPORT_INVALID_JSON",
                message="유효하지 않은 JSON 형식입니다.",
            ).model_dump(),
        )

    try:
        profile = await service.import_profile(data, file_size_bytes=body_size)
        return ProfileResponse.model_validate(profile)
    except ImportValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="IMPORT_INVALID_JSON",
                message=e.reason,
            ).model_dump(),
        )
