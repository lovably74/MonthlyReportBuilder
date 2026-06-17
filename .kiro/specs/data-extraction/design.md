# Design Document: 데이터 추출 (data-extraction)

## Overview

데이터 추출은 분류된 파일에서 문서 유형별 구조화 데이터를 추출하는 기능이다. 파일 형식별 파서(HWPX, DOCX, XLSX, PDF, Image)를 사용하여 핵심 필드를 JSON 형태로 추출한다.

### 핵심 설계 결정

1. **파서 전략 패턴**: 확장자별 Parser 인터페이스 구현체를 자동 선택.
2. **유형별 추출 스키마**: 문서 유형마다 추출 대상 필드가 다름 (스키마 정의).
3. **extracted_record JSON 저장**: 유연한 필드 구조를 위해 JSON TEXT 컬럼 사용.
4. **점진적 처리**: 개별 파일 실패가 전체를 중단하지 않음.

## Architecture

### 추출 파이프라인

```
classified files (from Spec 08)
  → ExtractionService.extract_job(job_id)
    → for each file:
      → ParserFactory.get_parser(extension)
      → ExtractionSchema.get_schema(classified_type)
      → parser.extract(file_path, schema)
      → extracted_record INSERT
  → job.status = EXTRACTED
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/extraction_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/extract` | POST | 추출 시작 |
| `/api/v1/jobs/{job_id}/records` | GET | 추출 결과 목록 |
| `/api/v1/jobs/{job_id}/records/{record_id}` | PUT | 추출 결과 수정 |

#### Service Layer

```python
class ExtractionService:
    async def extract_job(self, job_id: int) -> ExtractionSummary
    async def get_records(self, job_id: int, type_code: str = None) -> list[ExtractedRecord]
    async def update_record(self, record_id: int, data: dict) -> ExtractedRecord

class ParserFactory:
    def get_parser(self, extension: str) -> BaseParser

class BaseParser(ABC):
    @abstractmethod
    def extract(self, file_path: str, schema: dict) -> dict
```

### Parsers

| Parser | 대상 | 라이브러리 |
|--------|------|-----------|
| `HwpxDocParser` | .hwpx | zipfile + lxml |
| `DocxParser` | .docx | python-docx |
| `XlsxParser` | .xlsx | openpyxl |
| `PdfParser` | .pdf | pdfplumber |
| `ImageParser` | .jpg, .png | Pillow + piexif |

## Data Models

### SQLAlchemy ORM

```python
class ExtractedRecord(Base):
    __tablename__ = "extracted_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("collection_job.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("collected_file.id", ondelete="CASCADE"), nullable=False)
    type_code = Column(Text, nullable=False)
    extracted_data = Column(Text, nullable=False, default="{}")  # JSON
    is_manual_edited = Column(Boolean, default=False)
    extraction_status = Column(Text, default="success")  # success, partial, failed
    error_message = Column(Text)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
```

### 추출 스키마 예시

```python
EXTRACTION_SCHEMAS = {
    "official_doc": ["doc_number", "issue_date", "recipient", "title", "summary"],
    "meeting_minutes": ["meeting_date", "attendees", "agenda", "decisions"],
    "progress_report": ["progress_rate", "base_date", "actual_data"],
    "photo": ["taken_date", "gps", "description"],
}
```

## Correctness Properties

### Property 1: 추출 완전성
*For any* classified file에 대해, 추출 완료 후 extracted_record가 정확히 1개 존재해야 한다.

### Property 2: 스키마 준수
*For any* 추출된 extracted_data는 해당 type_code의 스키마 필드를 모두 포함해야 한다 (값이 빈 문자열이라도).

### Property 3: 수동 편집 보존
*For any* is_manual_edited=true인 레코드는 재추출 시에도 덮어쓰지 않아야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| JOB_NOT_FOUND | 404 | 존재하지 않는 job |
| NO_CLASSIFIED_FILES | 400 | 분류된 파일 없음 |
| PARSER_NOT_FOUND | 400 | 지원하지 않는 파일 형식 |
| EXTRACTION_FAILED | 500 | 파서 내부 오류 |

## Testing Strategy

- **Property Tests**: 추출 완전성, 스키마 준수, 수동 편집 보존
- **Unit Tests**: 각 Parser별 추출 정확성, 스키마 매핑
- **Integration Tests**: 전체 추출 플로우, 부분 실패 처리
- **Frontend Tests**: 추출 결과 테이블, 수동 편집 폼
