# Design Document: 취합 문서 샘플 등록 (document-sample)

## Overview

취합 문서 샘플 등록은 15개 문서 유형별 분류 기준(키워드, 유사도 임계값, 확장자)과 샘플 파일을 관리하는 기능이다. 이 설정은 Spec 08(document-classification)의 자동 분류 엔진이 참조하는 핵심 기준 데이터이다.

### 핵심 설계 결정

1. **15개 기본 유형 자동 생성**: 프로필 최초 생성 시 15개 document_type_config를 기본값으로 자동 생성한다.
2. **샘플 파일 저장**: `{DATA_DIR}/samples/{profile_id}/{type_code}/`에 물리 파일 저장.
3. **프로필 종속**: profile_id FK로 프로필에 종속, CASCADE 삭제.
4. **키워드 JSON 저장**: include_keywords, exclude_keywords를 JSON 배열로 TEXT 컬럼에 저장.

## Architecture

### 서버 레이어 구조

```
API Layer (document_sample_router.py)
  ↓
Service Layer (document_sample_service.py)
  ↓
Repository Layer (document_sample_repository.py)
  ↓
Database (document_type_config, document_sample 테이블)
```

### 파일 시스템 구조

```
{DATA_DIR}/samples/{profile_id}/{type_code}/
  ├── sample_001.hwpx
  ├── sample_002.docx
  └── ...
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/document_sample_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/document-types` | GET | 문서 유형 목록 조회 |
| `/api/v1/document-types/{type_id}` | GET | 문서 유형 상세 조회 |
| `/api/v1/document-types/{type_id}` | PUT | 문서 유형 설정 수정 |
| `/api/v1/document-types/{type_id}/samples` | GET | 샘플 목록 조회 |
| `/api/v1/document-types/{type_id}/samples` | POST | 샘플 업로드 |
| `/api/v1/document-types/{type_id}/samples/{sample_id}` | DELETE | 샘플 삭제 |

#### Service Layer (`app/services/document_sample_service.py`)

```python
class DocumentSampleService:
    async def initialize_types(self, profile_id: int) -> list[DocumentTypeConfig]
    async def list_types(self, profile_id: int) -> list[DocumentTypeConfig]
    async def update_type(self, type_id: int, data: TypeConfigUpdate) -> DocumentTypeConfig
    async def upload_sample(self, type_id: int, file: UploadFile) -> DocumentSample
    async def delete_sample(self, sample_id: int) -> None
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `DocumentSampleTab` | 문서 샘플 탭 컨테이너 |
| `DocumentTypeList` | 15개 유형 목록 (활성 상태, 샘플 수) |
| `TypeConfigForm` | 키워드, 유사도, 확장자 설정 폼 |
| `SampleFileList` | 샘플 파일 목록 (업로드/삭제) |

## Data Models

### SQLAlchemy ORM

```python
class DocumentTypeConfig(Base):
    __tablename__ = "document_type_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("settings_profile.id", ondelete="CASCADE"), nullable=False)
    type_code = Column(Text, nullable=False)  # e.g. "official_doc", "meeting_minutes"
    display_name = Column(Text, nullable=False)
    include_keywords = Column(Text, default="[]")  # JSON array
    exclude_keywords = Column(Text, default="[]")  # JSON array
    supported_extensions = Column(Text, default="[]")  # JSON array
    similarity_threshold = Column(Float, default=0.7)
    generate_ledger = Column(Boolean, default=False)
    include_in_appendix = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

class DocumentSample(Base):
    __tablename__ = "document_sample"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_config_id = Column(Integer, ForeignKey("document_type_config.id", ondelete="CASCADE"), nullable=False)
    original_file_name = Column(Text, nullable=False)
    stored_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(Text, nullable=False)
```

### TypeScript 인터페이스

```typescript
interface DocumentTypeConfig {
  id: number;
  profile_id: number;
  type_code: string;
  display_name: string;
  include_keywords: string[];
  exclude_keywords: string[];
  supported_extensions: string[];
  similarity_threshold: number;
  generate_ledger: boolean;
  include_in_appendix: boolean;
  is_active: boolean;
}

interface DocumentSample {
  id: number;
  type_config_id: number;
  original_file_name: string;
  file_size: number;
  uploaded_at: string;
}
```

## Correctness Properties

### Property 1: 키워드 라운드트립
*For any* 유효한 키워드 목록을 저장 후 조회하면, 저장한 키워드 목록과 동일한 결과가 반환되어야 한다.

### Property 2: 유사도 임계값 범위
*For any* similarity_threshold 설정 시, 0.0~1.0 범위를 벗어나는 값은 거부되어야 한다.

### Property 3: 샘플 수 제한
*For any* 문서 유형에 5개 이상의 샘플이 이미 존재할 때 추가 업로드를 시도하면, 시스템은 거부해야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| TYPE_NOT_FOUND | 404 | 존재하지 않는 문서 유형 ID |
| SAMPLE_LIMIT_EXCEEDED | 400 | 유형별 샘플 5개 초과 |
| SAMPLE_TOO_LARGE | 413 | 50MB 초과 |
| INVALID_THRESHOLD | 422 | 유사도 임계값 범위 초과 |
| KEYWORD_LIMIT_EXCEEDED | 422 | 키워드 50개 초과 |

## Testing Strategy

- **Property Tests**: 키워드 라운드트립, 임계값 범위 검증, 샘플 수 제한
- **Unit Tests**: 기본 유형 자동 생성, 키워드 파싱, 파일 저장 경로 생성
- **Integration Tests**: 샘플 업로드→조회→삭제 플로우, 프로필 삭제 CASCADE
- **Frontend Tests**: TypeConfigForm 유효성 검증, SampleFileList 렌더링
