"""Tests for error handlers and ErrorCodes.

Verifies that each custom exception type returns the correct HTTP status code
and error response format when raised during request handling.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.error_handlers import (
    ErrorCodes,
    register_exception_handlers,
    _determine_import_error_code,
    _determine_validation_error_code,
)
from app.core.exceptions import (
    CopyNameExhaustedError,
    ImportValidationError,
    LastProfileDeleteError,
    ProfileNameDuplicateError,
    ProfileNotFoundError,
)


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI app with exception handlers registered."""
    app = FastAPI(debug=False)
    register_exception_handlers(app)

    @app.get("/raise-not-found")
    async def raise_not_found():
        raise ProfileNotFoundError(profile_id=999)

    @app.get("/raise-duplicate")
    async def raise_duplicate():
        raise ProfileNameDuplicateError(name="테스트 프로필")

    @app.get("/raise-last-delete")
    async def raise_last_delete():
        raise LastProfileDeleteError()

    @app.get("/raise-import-invalid-json")
    async def raise_import_invalid_json():
        raise ImportValidationError(reason="JSON 파싱 실패: 유효하지 않은 형식")

    @app.get("/raise-import-missing-field")
    async def raise_import_missing_field():
        raise ImportValidationError(reason="필수 필드 name 누락")

    @app.get("/raise-import-file-too-large")
    async def raise_import_file_too_large():
        raise ImportValidationError(reason="파일 크기가 10MB를 초과합니다.")

    @app.get("/raise-copy-exhausted")
    async def raise_copy_exhausted():
        raise CopyNameExhaustedError(original_name="원본 프로필")

    @app.get("/raise-generic")
    async def raise_generic():
        raise RuntimeError("Unexpected database connection failure")

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client for the test app."""
    return TestClient(test_app, raise_server_exceptions=False)


class TestErrorCodes:
    """ErrorCodes 클래스의 상수 정의 검증."""

    def test_all_error_codes_defined(self):
        """모든 필수 에러 코드가 정의되어 있는지 확인."""
        assert ErrorCodes.PROFILE_NAME_REQUIRED == "PROFILE_NAME_REQUIRED"
        assert ErrorCodes.PROFILE_NAME_TOO_LONG == "PROFILE_NAME_TOO_LONG"
        assert ErrorCodes.PROFILE_DESC_TOO_LONG == "PROFILE_DESC_TOO_LONG"
        assert ErrorCodes.PROFILE_NAME_DUPLICATE == "PROFILE_NAME_DUPLICATE"
        assert ErrorCodes.PROFILE_NOT_FOUND == "PROFILE_NOT_FOUND"
        assert ErrorCodes.PROFILE_LAST_DELETE == "PROFILE_LAST_DELETE"
        assert ErrorCodes.IMPORT_INVALID_JSON == "IMPORT_INVALID_JSON"
        assert ErrorCodes.IMPORT_MISSING_FIELD == "IMPORT_MISSING_FIELD"
        assert ErrorCodes.IMPORT_FILE_TOO_LARGE == "IMPORT_FILE_TOO_LARGE"
        assert ErrorCodes.EXPORT_SAVE_FAILED == "EXPORT_SAVE_FAILED"
        assert ErrorCodes.DATABASE_ERROR == "DATABASE_ERROR"
        assert ErrorCodes.COPY_NAME_EXHAUSTED == "COPY_NAME_EXHAUSTED"


class TestProfileNotFoundHandler:
    """ProfileNotFoundError → 404 응답 검증."""

    def test_returns_404(self, client: TestClient):
        response = client.get("/raise-not-found")
        assert response.status_code == 404

    def test_error_code(self, client: TestClient):
        response = client.get("/raise-not-found")
        body = response.json()
        assert body["error_code"] == "PROFILE_NOT_FOUND"

    def test_message(self, client: TestClient):
        response = client.get("/raise-not-found")
        body = response.json()
        assert body["message"] == "해당 프로필을 찾을 수 없습니다."

    def test_detail_contains_id(self, client: TestClient):
        response = client.get("/raise-not-found")
        body = response.json()
        assert "999" in body["detail"]

    def test_field_is_none(self, client: TestClient):
        response = client.get("/raise-not-found")
        body = response.json()
        assert body["field"] is None


class TestProfileNameDuplicateHandler:
    """ProfileNameDuplicateError → 409 응답 검증."""

    def test_returns_409(self, client: TestClient):
        response = client.get("/raise-duplicate")
        assert response.status_code == 409

    def test_error_code(self, client: TestClient):
        response = client.get("/raise-duplicate")
        body = response.json()
        assert body["error_code"] == "PROFILE_NAME_DUPLICATE"

    def test_message(self, client: TestClient):
        response = client.get("/raise-duplicate")
        body = response.json()
        assert body["message"] == "동일한 이름의 프로필이 이미 존재합니다."

    def test_field_is_name(self, client: TestClient):
        response = client.get("/raise-duplicate")
        body = response.json()
        assert body["field"] == "name"


class TestLastProfileDeleteHandler:
    """LastProfileDeleteError → 400 응답 검증."""

    def test_returns_400(self, client: TestClient):
        response = client.get("/raise-last-delete")
        assert response.status_code == 400

    def test_error_code(self, client: TestClient):
        response = client.get("/raise-last-delete")
        body = response.json()
        assert body["error_code"] == "PROFILE_LAST_DELETE"

    def test_message(self, client: TestClient):
        response = client.get("/raise-last-delete")
        body = response.json()
        assert "마지막 프로필은 삭제할 수 없습니다" in body["message"]

    def test_field_is_none(self, client: TestClient):
        response = client.get("/raise-last-delete")
        body = response.json()
        assert body["field"] is None


class TestImportValidationHandler:
    """ImportValidationError → 400 응답 검증 (여러 이유별)."""

    def test_invalid_json_returns_400(self, client: TestClient):
        response = client.get("/raise-import-invalid-json")
        assert response.status_code == 400

    def test_invalid_json_error_code(self, client: TestClient):
        response = client.get("/raise-import-invalid-json")
        body = response.json()
        assert body["error_code"] == "IMPORT_INVALID_JSON"

    def test_invalid_json_message(self, client: TestClient):
        response = client.get("/raise-import-invalid-json")
        body = response.json()
        assert body["message"] == "유효하지 않은 JSON 파일입니다."

    def test_missing_field_error_code(self, client: TestClient):
        response = client.get("/raise-import-missing-field")
        body = response.json()
        assert body["error_code"] == "IMPORT_MISSING_FIELD"

    def test_missing_field_message(self, client: TestClient):
        response = client.get("/raise-import-missing-field")
        body = response.json()
        assert body["message"] == "필수 항목(프로필명)이 누락되었습니다."

    def test_file_too_large_error_code(self, client: TestClient):
        response = client.get("/raise-import-file-too-large")
        body = response.json()
        assert body["error_code"] == "IMPORT_FILE_TOO_LARGE"

    def test_file_too_large_message(self, client: TestClient):
        response = client.get("/raise-import-file-too-large")
        body = response.json()
        assert body["message"] == "파일 크기가 10MB를 초과합니다."

    def test_detail_contains_reason(self, client: TestClient):
        response = client.get("/raise-import-invalid-json")
        body = response.json()
        assert "JSON 파싱 실패" in body["detail"]


class TestCopyNameExhaustedHandler:
    """CopyNameExhaustedError → 409 응답 검증."""

    def test_returns_409(self, client: TestClient):
        response = client.get("/raise-copy-exhausted")
        assert response.status_code == 409

    def test_error_code(self, client: TestClient):
        response = client.get("/raise-copy-exhausted")
        body = response.json()
        assert body["error_code"] == "COPY_NAME_EXHAUSTED"

    def test_message(self, client: TestClient):
        response = client.get("/raise-copy-exhausted")
        body = response.json()
        assert "복사본 이름을 생성할 수 없습니다" in body["message"]

    def test_field_is_none(self, client: TestClient):
        response = client.get("/raise-copy-exhausted")
        body = response.json()
        assert body["field"] is None


class TestGenericExceptionHandler:
    """Generic Exception → 500 응답 검증."""

    def test_returns_500(self, client: TestClient):
        response = client.get("/raise-generic")
        assert response.status_code == 500

    def test_error_code(self, client: TestClient):
        response = client.get("/raise-generic")
        body = response.json()
        assert body["error_code"] == "DATABASE_ERROR"

    def test_message(self, client: TestClient):
        response = client.get("/raise-generic")
        body = response.json()
        assert body["message"] == "서버 내부 오류가 발생했습니다."

    def test_field_is_none(self, client: TestClient):
        response = client.get("/raise-generic")
        body = response.json()
        assert body["field"] is None


class TestRequestValidationHandler:
    """RequestValidationError (Pydantic) → 422 응답 검증."""

    @pytest.fixture
    def validation_app(self) -> FastAPI:
        """Create an app with a Pydantic-validated endpoint."""
        from pydantic import BaseModel, Field

        app = FastAPI()
        register_exception_handlers(app)

        class TestInput(BaseModel):
            name: str = Field(..., min_length=1, max_length=50)
            description: str = Field(default="", max_length=200)

        @app.post("/validate")
        async def validate_input(data: TestInput):
            return {"name": data.name}

        return app

    @pytest.fixture
    def validation_client(self, validation_app: FastAPI) -> TestClient:
        return TestClient(validation_app)

    def test_missing_name_returns_422(self, validation_client: TestClient):
        response = validation_client.post("/validate", json={})
        assert response.status_code == 422

    def test_missing_name_has_error_code(self, validation_client: TestClient):
        response = validation_client.post("/validate", json={})
        body = response.json()
        assert body["error_code"] == "PROFILE_NAME_REQUIRED"

    def test_missing_name_has_field(self, validation_client: TestClient):
        response = validation_client.post("/validate", json={})
        body = response.json()
        assert body["field"] == "name"

    def test_response_format_has_all_fields(self, validation_client: TestClient):
        """응답에 error_code, message, detail, field 필드가 모두 존재하는지 확인."""
        response = validation_client.post("/validate", json={})
        body = response.json()
        assert "error_code" in body
        assert "message" in body
        assert "detail" in body
        assert "field" in body


class TestDetermineImportErrorCode:
    """_determine_import_error_code 유틸 함수 검증."""

    def test_json_keyword(self):
        assert _determine_import_error_code("Invalid JSON format") == ErrorCodes.IMPORT_INVALID_JSON

    def test_parse_keyword(self):
        assert _determine_import_error_code("JSON 파싱 실패") == ErrorCodes.IMPORT_INVALID_JSON

    def test_missing_keyword(self):
        assert _determine_import_error_code("필수 필드 누락") == ErrorCodes.IMPORT_MISSING_FIELD

    def test_name_keyword(self):
        assert _determine_import_error_code("name field is missing") == ErrorCodes.IMPORT_MISSING_FIELD

    def test_size_keyword(self):
        assert _determine_import_error_code("파일 크기 초과") == ErrorCodes.IMPORT_FILE_TOO_LARGE

    def test_10mb_keyword(self):
        assert _determine_import_error_code("File exceeds 10MB limit") == ErrorCodes.IMPORT_FILE_TOO_LARGE

    def test_unknown_defaults_to_invalid_json(self):
        assert _determine_import_error_code("some unknown reason") == ErrorCodes.IMPORT_INVALID_JSON


class TestDetermineValidationErrorCode:
    """_determine_validation_error_code 유틸 함수 검증."""

    def test_name_field_required(self):
        assert _determine_validation_error_code("name", "Field required") == ErrorCodes.PROFILE_NAME_REQUIRED

    def test_name_field_too_long(self):
        assert _determine_validation_error_code("name", "String should have at most 50 characters") == ErrorCodes.PROFILE_NAME_TOO_LONG

    def test_description_field_too_long(self):
        assert _determine_validation_error_code("description", "String should have at most 200 characters") == ErrorCodes.PROFILE_DESC_TOO_LONG

    def test_unknown_field_defaults(self):
        assert _determine_validation_error_code("unknown", "some error") == ErrorCodes.PROFILE_NAME_REQUIRED


class TestErrorResponseFormat:
    """모든 에러 응답이 ErrorResponse 스키마 형식을 준수하는지 검증."""

    @pytest.fixture
    def all_error_endpoints(self) -> list[str]:
        return [
            "/raise-not-found",
            "/raise-duplicate",
            "/raise-last-delete",
            "/raise-import-invalid-json",
            "/raise-import-missing-field",
            "/raise-import-file-too-large",
            "/raise-copy-exhausted",
            "/raise-generic",
        ]

    def test_all_responses_have_required_keys(
        self, client: TestClient, all_error_endpoints: list[str]
    ):
        """모든 에러 응답이 error_code, message, detail, field 키를 포함."""
        for endpoint in all_error_endpoints:
            response = client.get(endpoint)
            body = response.json()
            assert "error_code" in body, f"{endpoint} missing error_code"
            assert "message" in body, f"{endpoint} missing message"
            assert "detail" in body, f"{endpoint} missing detail"
            assert "field" in body, f"{endpoint} missing field"

    def test_error_codes_are_strings(
        self, client: TestClient, all_error_endpoints: list[str]
    ):
        """모든 error_code 값이 문자열 타입."""
        for endpoint in all_error_endpoints:
            response = client.get(endpoint)
            body = response.json()
            assert isinstance(body["error_code"], str), f"{endpoint} error_code not string"

    def test_messages_are_strings(
        self, client: TestClient, all_error_endpoints: list[str]
    ):
        """모든 message 값이 문자열 타입."""
        for endpoint in all_error_endpoints:
            response = client.get(endpoint)
            body = response.json()
            assert isinstance(body["message"], str), f"{endpoint} message not string"
