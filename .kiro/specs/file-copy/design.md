# Design Document: 파일 복사 (file-copy)

## Overview

파일 복사는 검색된 파일을 작업폴더로 복사하고 collection_job/collected_file 레코드를 생성하는 기능이다. 이후 모든 분류·추출·생성 작업은 이 복사본을 대상으로 수행된다.

### 핵심 설계 결정

1. **원본 보존**: 원본 파일은 절대 수정하지 않고 작업폴더에 복사본으로 작업.
2. **충돌 처리 정책**: rename(기본), skip, overwrite 3가지 정책 지원.
3. **작업 단위(job)**: collection_job이 전체 파이프라인의 추적 단위.
4. **점진적 복사**: 개별 파일 실패가 전체 작업을 중단하지 않음.

## Architecture

### 데이터 흐름

```
scan_result (from Spec 06)
  → FileCopyService.copy_files(job_id, scan_result)
    → WorkFolderManager.create(work_folder_path, pattern)
    → for each file: copy → collected_file INSERT
  → collection_job.status = COPIED
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/file_copy_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs` | POST | collection_job 생성 |
| `/api/v1/jobs/{job_id}` | GET | job 상태 조회 |
| `/api/v1/jobs/{job_id}/copy` | POST | 파일 복사 시작 |
| `/api/v1/jobs/{job_id}/files` | GET | 복사된 파일 목록 |

#### Service Layer

```python
class FileCopyService:
    async def create_job(self, profile_id: int) -> CollectionJob
    async def start_copy(self, job_id: int, scan_result: ScanResult) -> CopyResult
    async def get_job_status(self, job_id: int) -> CollectionJob
    async def retry_failed(self, job_id: int) -> CopyResult

class WorkFolderManager:
    def create_folder(self, base_path: str, pattern: str, context: dict) -> str
    def resolve_conflict(self, dest_path: str, policy: str) -> str
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `CopyPanel` | 복사 실행 및 진행률 패널 |
| `CopyProgress` | 진행률 바 + 파일 카운터 |
| `CopyResultSummary` | 복사 결과 (성공/실패/스킵 건수) |
| `ConflictPolicySelect` | 충돌 처리 정책 선택 |

## Data Models

### SQLAlchemy ORM

```python
class CollectionJob(Base):
    __tablename__ = "collection_job"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("settings_profile.id"), nullable=False)
    status = Column(Text, nullable=False, default="CREATED")  # CREATED, SCANNING, COPIED, CLASSIFIED, EXTRACTED, REVIEWED, COMPLETED, FAILED
    work_folder = Column(Text, default="")
    total_files = Column(Integer, default=0)
    copied_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    started_at = Column(Text, nullable=False)
    completed_at = Column(Text)
    updated_at = Column(Text, nullable=False)

class CollectedFile(Base):
    __tablename__ = "collected_file"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("collection_job.id", ondelete="CASCADE"), nullable=False)
    original_path = Column(Text, nullable=False)
    copied_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    extension = Column(Text, nullable=False)
    classified_type = Column(Text)
    confidence = Column(Float)
    classification_method = Column(Text)
    copied_at = Column(Text, nullable=False)
```

### TypeScript 인터페이스

```typescript
interface CollectionJob {
  id: number;
  profile_id: number;
  status: string;
  work_folder: string;
  total_files: number;
  copied_files: number;
  failed_files: number;
  started_at: string;
  completed_at: string | null;
}

interface CollectedFile {
  id: number;
  job_id: number;
  original_path: string;
  copied_path: string;
  file_size: number;
  extension: string;
  classified_type: string | null;
  confidence: number | null;
}
```

## Correctness Properties

### Property 1: 복사 완전성
*For any* 스캔 결과의 N개 파일에 대해 복사 완료 후, copied_files + failed_files = N이어야 한다.

### Property 2: 충돌 처리 일관성
*For any* rename 정책에서 동일 파일명이 K번 충돌하면, 결과 파일명은 모두 고유해야 한다.

### Property 3: 작업 상태 전이 유효성
*For any* collection_job의 상태 전이는 CREATED→SCANNING→COPIED→CLASSIFIED→... 순서를 따라야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| JOB_NOT_FOUND | 404 | 존재하지 않는 job_id |
| WORK_FOLDER_NOT_WRITABLE | 400 | 작업폴더 쓰기 권한 없음 |
| COPY_ALREADY_IN_PROGRESS | 409 | 이미 복사 진행 중 |
| NO_SCAN_RESULT | 400 | 스캔 결과 없음 |

## Testing Strategy

- **Property Tests**: 복사 완전성, 충돌 처리 고유성, 상태 전이
- **Unit Tests**: WorkFolderManager 폴더 생성, 충돌 처리 rename 로직
- **Integration Tests**: 전체 복사 플로우, 실패 재시도
- **Frontend Tests**: CopyProgress 업데이트, ConflictPolicySelect
