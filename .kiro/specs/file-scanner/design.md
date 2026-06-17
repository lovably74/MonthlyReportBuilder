# Design Document: 파일 검색 (file-scanner)

## Overview

파일 검색은 설정된 루트 경로 하위의 파일을 재귀 탐색하고, 날짜/확장자 필터를 적용하여 취합 대상 파일 목록을 생성하는 서버 사이드 기능이다. 검색 결과는 임시 저장되어 Spec 07(file-copy)에서 참조된다.

### 핵심 설계 결정

1. **서버 실행**: 파일 검색은 서버에서 수행 (대상 경로가 서버 로컬 파일시스템).
2. **비동기 스캔**: 대용량 폴더 검색을 위해 비동기 작업으로 처리하고 진행률을 SSE로 전달.
3. **날짜 추출 전략**: 파일명 패턴 > EXIF > 수정일 우선순위.
4. **결과 임시 저장**: 검색 결과를 scan_result JSON 파일로 저장하여 후속 작업에서 참조.

## Architecture

### 데이터 흐름

```
Client → POST /api/v1/jobs/{job_id}/scan
  → ScanService.start_scan(root_path, filters)
    → FileWalker.walk(root_path)
      → DateExtractor.extract(file)
      → ExtensionFilter.apply(file)
    → scan_result JSON 저장
  ← SSE: 진행률 이벤트
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/scanner_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/scan` | POST | 스캔 시작 |
| `/api/v1/jobs/{job_id}/scan/status` | GET | 스캔 상태 조회 |
| `/api/v1/jobs/{job_id}/scan/result` | GET | 스캔 결과 조회 |

#### Service Layer

```python
class ScanService:
    async def start_scan(self, job_id: int, config: ScanConfig) -> ScanJob
    async def get_status(self, job_id: int) -> ScanStatus
    async def get_result(self, job_id: int) -> ScanResult

class FileWalker:
    def walk(self, root_path: str, skip_symlinks: bool = True) -> Generator[FileInfo]

class DateExtractor:
    def extract(self, file_path: str) -> date | None
    def from_filename(self, filename: str) -> date | None
    def from_exif(self, file_path: str) -> date | None
    def from_mtime(self, file_path: str) -> date
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `ScanPanel` | 스캔 실행 및 필터 설정 패널 |
| `DateRangeFilter` | 시작일~종료일 선택 |
| `ExtensionFilter` | 확장자 체크박스 목록 |
| `ScanProgress` | 진행률 표시 (파일 수, 현재 폴더) |
| `ScanResultSummary` | 결과 요약 (총 파일 수, 크기, 유형별 통계) |

## Data Models

### Pydantic Schemas

```python
class ScanConfig(BaseModel):
    root_path: str
    start_date: date | None = None
    end_date: date | None = None
    extensions: list[str] = []

class FileInfo(BaseModel):
    path: str
    size: int
    modified_at: str
    estimated_date: str | None
    extension: str

class ScanResult(BaseModel):
    job_id: int
    total_files: int
    total_size: int
    files: list[FileInfo]
    stats: dict[str, int]  # extension -> count
    scan_duration_ms: int
```

## Correctness Properties

### Property 1: 확장자 필터 정확성
*For any* 확장자 필터가 설정된 경우, 결과에 포함된 모든 파일의 확장자는 필터 목록에 포함되어야 한다.

### Property 2: 날짜 필터 범위 준수
*For any* 날짜 필터가 설정된 경우, estimated_date가 존재하는 결과 파일은 모두 시작일~종료일 범위 내여야 한다.

### Property 3: 재귀 완전성
*For any* 접근 가능한 디렉토리의 파일은 필터 조건만 충족하면 반드시 결과에 포함되어야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| ROOT_PATH_NOT_FOUND | 400 | 루트 경로 미존재 |
| ROOT_PATH_NOT_CONFIGURED | 400 | 루트 경로 미설정 |
| SCAN_IN_PROGRESS | 409 | 이미 스캔 진행 중 |
| ACCESS_DENIED | 403 | 경로 접근 권한 없음 |

## Testing Strategy

- **Property Tests**: 확장자 필터, 날짜 필터 정확성, 재귀 완전성
- **Unit Tests**: DateExtractor 패턴 인식, FileWalker 심볼릭 링크 무시
- **Integration Tests**: 실제 폴더 구조에서 스캔→결과 검증
- **Frontend Tests**: DateRangeFilter 입력, ScanProgress 업데이트
