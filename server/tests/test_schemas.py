"""Tests for profile Pydantic schemas.

Validates ProfileCreate, ProfileUpdate, ProfileResponse,
ProfileListResponse, and ErrorResponse schema behavior.
"""

import pytest
from pydantic import ValidationError

from app.schemas.profile import (
    ErrorResponse,
    ProfileCreate,
    ProfileListResponse,
    ProfileResponse,
    ProfileUpdate,
)


class TestProfileCreate:
    """ProfileCreate 스키마 검증 테스트."""

    def test_valid_name_and_description(self):
        """유효한 이름과 설명으로 생성 가능."""
        schema = ProfileCreate(name="테스트 프로필", description="설명 텍스트")
        assert schema.name == "테스트 프로필"
        assert schema.description == "설명 텍스트"

    def test_valid_name_only(self):
        """이름만 입력해도 생성 가능 (description 기본값 빈 문자열)."""
        schema = ProfileCreate(name="프로필A")
        assert schema.name == "프로필A"
        assert schema.description == ""

    def test_name_whitespace_stripped(self):
        """이름 앞뒤 공백이 자동으로 제거됨."""
        schema = ProfileCreate(name="  공백 프로필  ")
        assert schema.name == "공백 프로필"

    def test_name_with_tabs_stripped(self):
        """이름 앞뒤 탭/개행 공백이 제거됨."""
        schema = ProfileCreate(name="\t탭 프로필\n")
        assert schema.name == "탭 프로필"

    def test_empty_name_rejected(self):
        """빈 이름은 거부됨."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCreate(name="")
        errors = exc_info.value.errors()
        assert any(e["type"] == "string_too_short" for e in errors)

    def test_whitespace_only_name_rejected(self):
        """공백만으로 구성된 이름은 거부됨."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCreate(name="   ")
        errors = exc_info.value.errors()
        assert any("프로필명은 필수 입력값입니다" in str(e) for e in errors)

    def test_name_exceeds_50_chars_rejected(self):
        """50자 초과 이름은 거부됨."""
        long_name = "가" * 51
        with pytest.raises(ValidationError):
            ProfileCreate(name=long_name)

    def test_name_exactly_50_chars_accepted(self):
        """정확히 50자 이름은 허용됨."""
        name_50 = "가" * 50
        schema = ProfileCreate(name=name_50)
        assert schema.name == name_50

    def test_name_1_char_accepted(self):
        """1자 이름은 허용됨."""
        schema = ProfileCreate(name="A")
        assert schema.name == "A"

    def test_description_exceeds_200_chars_rejected(self):
        """200자 초과 설명은 거부됨."""
        long_desc = "나" * 201
        with pytest.raises(ValidationError):
            ProfileCreate(name="valid", description=long_desc)

    def test_description_exactly_200_chars_accepted(self):
        """정확히 200자 설명은 허용됨."""
        desc_200 = "나" * 200
        schema = ProfileCreate(name="valid", description=desc_200)
        assert schema.description == desc_200

    def test_whitespace_padding_name_over_50_after_strip(self):
        """공백 포함 시 strip 후 50자 초과면 거부."""
        # 51 chars of content + padding
        inner = "가" * 51
        padded = f"  {inner}  "
        with pytest.raises(ValidationError):
            ProfileCreate(name=padded)


class TestProfileUpdate:
    """ProfileUpdate 스키마 검증 테스트."""

    def test_none_values_accepted(self):
        """name=None, description=None으로 유효함."""
        schema = ProfileUpdate()
        assert schema.name is None
        assert schema.description is None

    def test_valid_name_update(self):
        """유효한 이름으로 수정 가능."""
        schema = ProfileUpdate(name="수정된 프로필")
        assert schema.name == "수정된 프로필"

    def test_valid_description_update(self):
        """유효한 설명으로 수정 가능."""
        schema = ProfileUpdate(description="새 설명")
        assert schema.description == "새 설명"

    def test_name_whitespace_stripped(self):
        """수정 시 이름 앞뒤 공백 제거됨."""
        schema = ProfileUpdate(name="  수정 프로필  ")
        assert schema.name == "수정 프로필"

    def test_whitespace_only_name_rejected(self):
        """수정 시 공백만 입력하면 거부됨."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileUpdate(name="   ")
        errors = exc_info.value.errors()
        assert any("프로필명은 필수 입력값입니다" in str(e) for e in errors)

    def test_name_exceeds_50_chars_rejected(self):
        """수정 시 50자 초과 이름 거부됨."""
        with pytest.raises(ValidationError):
            ProfileUpdate(name="가" * 51)

    def test_description_exceeds_200_chars_rejected(self):
        """수정 시 200자 초과 설명 거부됨."""
        with pytest.raises(ValidationError):
            ProfileUpdate(description="나" * 201)

    def test_both_fields_valid(self):
        """이름과 설명 동시 수정 가능."""
        schema = ProfileUpdate(name="새이름", description="새설명")
        assert schema.name == "새이름"
        assert schema.description == "새설명"


class TestProfileResponse:
    """ProfileResponse 스키마 검증 테스트."""

    def test_valid_response(self):
        """모든 필드가 있는 유효한 응답."""
        response = ProfileResponse(
            id=1,
            name="프로필1",
            description="설명",
            is_default=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert response.id == 1
        assert response.name == "프로필1"
        assert response.is_default is True

    def test_from_attributes(self):
        """ORM 객체에서 변환 가능 (from_attributes=True)."""

        class FakeORM:
            id = 1
            name = "ORM프로필"
            description = "ORM설명"
            is_default = False
            created_at = "2024-06-01T12:00:00"
            updated_at = "2024-06-01T12:00:00"

        response = ProfileResponse.model_validate(FakeORM())
        assert response.id == 1
        assert response.name == "ORM프로필"
        assert response.is_default is False


class TestProfileListResponse:
    """ProfileListResponse 스키마 검증 테스트."""

    def test_empty_list(self):
        """빈 프로필 목록."""
        response = ProfileListResponse(profiles=[], total=0)
        assert response.profiles == []
        assert response.total == 0

    def test_list_with_profiles(self):
        """프로필이 포함된 목록."""
        profiles = [
            ProfileResponse(
                id=1,
                name="프로필1",
                description="",
                is_default=True,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            ),
            ProfileResponse(
                id=2,
                name="프로필2",
                description="두번째",
                is_default=False,
                created_at="2024-01-02T00:00:00",
                updated_at="2024-01-02T00:00:00",
            ),
        ]
        response = ProfileListResponse(profiles=profiles, total=2)
        assert len(response.profiles) == 2
        assert response.total == 2


class TestErrorResponse:
    """ErrorResponse 스키마 검증 테스트."""

    def test_minimal_error(self):
        """필수 필드만으로 에러 응답 생성."""
        error = ErrorResponse(
            error_code="PROFILE_NAME_REQUIRED",
            message="프로필명은 필수 입력값입니다.",
        )
        assert error.error_code == "PROFILE_NAME_REQUIRED"
        assert error.message == "프로필명은 필수 입력값입니다."
        assert error.detail is None
        assert error.field is None

    def test_full_error(self):
        """모든 필드를 포함한 에러 응답."""
        error = ErrorResponse(
            error_code="PROFILE_NAME_TOO_LONG",
            message="프로필명은 50자를 초과할 수 없습니다.",
            detail="입력된 길이: 55자",
            field="name",
        )
        assert error.error_code == "PROFILE_NAME_TOO_LONG"
        assert error.detail == "입력된 길이: 55자"
        assert error.field == "name"
