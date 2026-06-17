# Design Document: 작업폴더 설정 (folder-config)

## Overview

작업폴더 설정은 파일 검색 루트 경로, 작업폴더 경로, 결과물 저장 경로, 파일명 규칙을 프로필별로 관리하는 기능이다. 이 설정값은 파일 스캔(Spec 06), 파일 복사(Spec 07), 보고서 출력(Spec 15) 등 다수의 후속 기능에서 참조된다.

### 핵심 설계 결정

1. **단일 테이블**: `folder_config` 테이블에 모든 경로와 규칙을 저장. 프로필당 1개 레코드.
2. **경로 검증 분리**: 저장 시 검증이 아닌 조회 시 검증(경로는 언제든 변경될 수 있으므로).
3. **변수 치환 패턴**: `{PROJECT}`, `{YYYY}`, `{MM}`, `{ROUND}`, `{DATE}` 변수 지원.
4. **Tauri 폴더 선택**: 클라이언트에서 Tauri dialog API로 폴더를 선택하고 경로 문자열을 서버에 전달.

## Architecture

### 서버 레이어 구조

```
API Layer (folder_config_router.py)
  ↓
Service Layer (folder_config_service.py)
  ↓
Repository Layer (folder_config_repository.py)
  ↓
Database (folder_config 테이블)
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/folder_config_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/folder-config` | GET | 프로필의 폴더 설정 조회 |
| `/api/v1/folder-config` | PUT | 폴더 설정 저장/수정 |
| `/api/v1/folder-config/validate` | POST | 경로 검증 요청 |

#### Service Layer (`app/services/folder_config_service.py`)

```python
class FolderConfigService:
    async def get_config(self, profile_id: int) -> FolderConfig
    async def upsert_config(self, profile_id: int, data: FolderConfigUpdate) -> FolderConfig
    async def validate_paths(self, profile_id: int) -> PathValidationResult
    def preview_filename(self, naming_rule: str, context: dict) -> str
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `FolderConfigTab` | 폴더 설정 탭 컨테이너 |
| `PathInput` | 경로 입력 + 폴더 선택 버튼 + 상태 아이콘 |
| `NamingRuleEditor` | 파일명 규칙 편집기 + 미리보기 |
| `PathValidator` | 모든 경로 검증 결과 표시 |

## Data Models

### SQLAlchemy ORM

```python
class FolderConfig(Base):
    __tablename__ = "folder_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("settings_profile.id", ondelete="CASCADE"), nullable=False, unique=True)
    root_path = Column(Text, default="")
    work_folder_path = Column(Text, default="")
    work_folder_pattern = Column(Text, default="{YYYYMM}")
    output_path = Column(Text, default="")
    naming_rule = Column(Text, default="{PROJECT}_{YYYYMM}_월간보고서.hwpx")
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
```

### TypeScript 인터페이스

```typescript
interface FolderConfig {
  id: number;
  profile_id: number;
  root_path: string;
  work_folder_path: string;
  work_folder_pattern: string;
  output_path: string;
  naming_rule: string;
}

interface PathValidationResult {
  root_path: { exists: boolean; readable: boolean };
  work_folder_path: { exists: boolean; writable: boolean };
  output_path: { exists: boolean; writable: boolean };
}
```

## Correctness Properties

### Property 1: 경로 정규화 일관성
*For any* 유효한 절대 경로를 설정하면, 조회 시 동일한 정규화된 절대 경로가 반환되어야 한다.

### Property 2: 파일명 규칙 변수 치환
*For any* 유효한 naming_rule과 context 변수 집합에 대해, preview_filename의 결과에 파일시스템 금지 문자가 포함되지 않아야 한다.

### Property 3: 프로필당 단일 설정
*For any* 프로필에 대해 folder_config는 정확히 0개 또는 1개만 존재해야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| PROFILE_NOT_FOUND | 404 | 존재하지 않는 프로필 |
| INVALID_NAMING_RULE | 422 | 금지 문자 포함 파일명 규칙 |
| PATH_NOT_ACCESSIBLE | 400 | 쓰기 권한 없는 경로 |

## Testing Strategy

- **Property Tests**: 경로 정규화 라운드트립, 파일명 변수 치환 무결성
- **Unit Tests**: 경로 검증 로직, naming_rule 미리보기
- **Integration Tests**: 설정 저장→조회 플로우, 프로필 삭제 CASCADE
- **Frontend Tests**: PathInput 폴더 선택, NamingRuleEditor 미리보기
