"""Pydantic request/response schemas for profile management.

Defines validation schemas for profile CRUD operations including:
- ProfileCreate: 프로필 생성 요청 스키마
- ProfileUpdate: 프로필 수정 요청 스키마
- ProfileResponse: 프로필 응답 스키마
- ProfileListResponse: 프로필 목록 응답 스키마
- ErrorResponse: 에러 응답 스키마
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileCreate(BaseModel):
    """프로필 생성 요청 스키마.

    Attributes:
        name: 프로필명 (공백 제거 후 1~50자, 필수)
        description: 프로필 설명 (최대 200자, 선택)
    """

    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """공백 제거 및 길이 검증."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("프로필명은 필수 입력값입니다.")
        if len(stripped) > 50:
            raise ValueError("프로필명은 50자를 초과할 수 없습니다.")
        return stripped


class ProfileUpdate(BaseModel):
    """프로필 수정 요청 스키마.

    Attributes:
        name: 프로필명 (공백 제거 후 1~50자, 선택)
        description: 프로필 설명 (최대 200자, 선택)
    """

    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """공백 제거 및 길이 검증 (None 허용)."""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("프로필명은 필수 입력값입니다.")
        if len(stripped) > 50:
            raise ValueError("프로필명은 50자를 초과할 수 없습니다.")
        return stripped


class ProfileResponse(BaseModel):
    """프로필 응답 스키마.

    Attributes:
        id: 프로필 고유 ID
        name: 프로필명
        description: 프로필 설명
        is_default: 기본 프로필 여부
        created_at: 생성 시각 (ISO 8601)
        updated_at: 수정 시각 (ISO 8601)
    """

    id: int
    name: str
    description: str
    is_default: bool
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class ProfileListResponse(BaseModel):
    """프로필 목록 응답 스키마.

    Attributes:
        profiles: 프로필 응답 목록
        total: 전체 프로필 수
    """

    profiles: list[ProfileResponse]
    total: int


class ErrorResponse(BaseModel):
    """에러 응답 스키마.

    Attributes:
        error_code: 머신 판독용 에러 코드
        message: 사용자 표시 메시지
        detail: 개발자용 상세 정보 (선택)
        field: 유효성 오류 시 필드명 (선택)
    """

    error_code: str
    message: str
    detail: str | None = None
    field: str | None = None
