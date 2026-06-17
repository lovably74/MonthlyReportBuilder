# Design Document: 최종 결과 파일 생성 (report-output)

## Overview

최종 결과 생성은 렌더링된 HWPX 보고서와 Excel 대장을 설정된 경로에 저장하고, 검증 리포트를 생성하는 기능이다. folder_config의 파일명 규칙을 적용하여 산출물 이름을 결정한다.

### 핵심 설계 결정

1. **3종 산출물**: HWPX 보고서 + Excel 대장 + 검증 리포트(TXT).
2. **파일명 규칙 적용**: folder_config.naming_rule의 변수를 치환.
3. **버전 충돌 방지**: 동일 파일명 존재 시 `_v{N}` 접미사.
4. **검증 3단계**: 정상/경고/오류로 분류.

## Architecture

### 출력 파이프라인

```
rendered HWPX (from Spec 11)
  → ReportOutputService.generate(job_id)
    → apply naming_rule → filename
    → copy HWPX to output_path
    → ExcelExporter.export(ledgers)
    → VerificationReporter.generate(job_id)
    → save report_generation record
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/report_output_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/output` | POST | 결과 생성 |
| `/api/v1/jobs/{job_id}/output` | GET | 결과 조회 |
| `/api/v1/jobs/{job_id}/output/verify` | GET | 검증 리포트 조회 |

#### Service Layer

```python
class ReportOutputService:
    async def generate_output(self, job_id: int) -> ReportOutputResult
    async def get_output(self, job_id: int) -> ReportOutputResult

class ExcelExporter:
    def export(self, ledgers: list[LedgerTable], output_path: str) -> str

class VerificationReporter:
    def generate(self, job_id: int) -> VerificationReport
```

## Data Models

### SQLAlchemy ORM

```python
class ReportGeneration(Base):
    __tablename__ = "report_generation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("collection_job.id", ondelete="CASCADE"), nullable=False)
    hwpx_path = Column(Text)
    excel_path = Column(Text)
    verification_path = Column(Text)
    status = Column(Text, default="success")  # success, warning, error
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(Text, nullable=False)
```

### Pydantic Schemas

```python
class ReportOutputResult(BaseModel):
    job_id: int
    hwpx_path: str
    excel_path: str
    verification_path: str
    status: str
    warnings: list[str]
    errors: list[str]

class VerificationReport(BaseModel):
    tags_replaced: int
    tags_missing: int
    tables_inserted: int
    tables_empty: int
    images_inserted: int
    images_missing: int
    summary_sections: int
    summary_missing: int
    overall_status: str  # 정상, 경고, 오류
```

## Correctness Properties

### Property 1: 산출물 완전성
*For any* 성공 status의 결과에서, hwpx_path, excel_path, verification_path는 모두 실제 파일이 존재해야 한다.

### Property 2: 파일명 규칙 준수
*For any* 생성된 파일의 이름은 naming_rule 패턴을 변수 치환한 결과와 일치해야 한다.

### Property 3: 검증 리포트 정확성
*For any* 검증 리포트의 tags_missing > 0이면, overall_status는 '경고' 또는 '오류'여야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| NO_RENDERED_FILE | 400 | 렌더링된 HWPX 없음 |
| OUTPUT_PATH_NOT_WRITABLE | 400 | 저장 경로 쓰기 불가 |
| EXCEL_GENERATION_FAILED | 500 | Excel 생성 실패 |

## Testing Strategy

- **Property Tests**: 산출물 완전성, 파일명 규칙, 검증 정확성
- **Unit Tests**: ExcelExporter 시트 생성, VerificationReporter 로직
- **Integration Tests**: 전체 출력 플로우, 버전 충돌 처리
