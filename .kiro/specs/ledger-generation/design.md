# Design Document: 대장 자동 생성 (ledger-generation)

## Overview

대장 생성은 extracted_record 데이터를 ledger_config의 컬럼 정의에 따라 테이블 형식으로 변환하는 기능이다. 생성된 대장 데이터는 JSON 배열로 HWPX 렌더러에 전달된다.

### 핵심 설계 결정

1. **데이터 매핑**: ledger_config.columns의 data_source를 extracted_data의 필드에 매핑.
2. **자동 번호 부여**: 첫 컬럼이 '번호'이면 정렬 후 1부터 순차 부여.
3. **형식 변환**: 날짜 YYYY.MM.DD, 숫자 천단위 구분자 자동 적용.
4. **JSON 출력**: `{header: string[], rows: string[][]}` 형식.

## Architecture

### 데이터 흐름

```
extracted_record (from Spec 09) + ledger_config (from Spec 05)
  → LedgerGenerationService.generate(job_id)
    → for each type_code with generate_ledger=true:
      → LedgerBuilder.build(records, config)
        → map data_source → extracted_data fields
        → sort by sort_columns
        → assign row numbers
        → format cells
      → save ledger_data JSON
  → 결과: type별 LedgerTable
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/ledger_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/ledgers` | POST | 대장 생성 시작 |
| `/api/v1/jobs/{job_id}/ledgers` | GET | 대장 데이터 조회 |
| `/api/v1/jobs/{job_id}/ledgers/{type_code}` | GET | 특정 유형 대장 조회 |

#### Service Layer

```python
class LedgerGenerationService:
    async def generate_ledgers(self, job_id: int) -> list[LedgerTable]
    async def get_ledger(self, job_id: int, type_code: str) -> LedgerTable

class LedgerBuilder:
    def build(self, records: list[ExtractedRecord], config: LedgerConfig) -> LedgerTable
    def format_date(self, value: str) -> str
    def format_number(self, value: str) -> str
```

## Data Models

### Pydantic Schemas

```python
class LedgerTable(BaseModel):
    type_code: str
    title: str
    header: list[str]
    rows: list[list[str]]
    total_rows: int

class LedgerGenerationResult(BaseModel):
    job_id: int
    ledgers: list[LedgerTable]
    total_types: int
    total_rows: int
```

## Correctness Properties

### Property 1: 데이터 행 수 일치
*For any* type_code에 대해, 대장의 rows 수는 해당 유형의 extracted_record 수와 일치해야 한다.

### Property 2: 번호 연속성
*For any* 자동 번호 부여 시, 번호는 1부터 시작하여 빈 번호 없이 연속이어야 한다.

### Property 3: 정렬 불변식
*For any* sort_columns가 설정된 대장에서, rows는 해당 컬럼 값의 지정 순서로 정렬되어야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| NO_EXTRACTED_DATA | 400 | 추출 데이터 없음 |
| NO_LEDGER_CONFIG | 400 | 대장 설정 없음 |
| FIELD_MAPPING_ERROR | 500 | data_source 매핑 실패 |

## Testing Strategy

- **Property Tests**: 행 수 일치, 번호 연속성, 정렬 불변식
- **Unit Tests**: format_date, format_number, 필드 매핑
- **Integration Tests**: 전체 생성 플로우, 빈 데이터 처리
