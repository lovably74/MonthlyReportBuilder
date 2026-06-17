# Design Document: 대장/사진대지 설정 (ledger-photo-config)

## Overview

대장/사진대지 설정은 문서 유형별 대장의 컬럼 구성과 사진대지의 레이아웃을 프로필별로 관리한다. 이 설정값은 Spec 10(ledger-generation)과 Spec 12(photo-board)에서 직접 참조된다.

### 핵심 설계 결정

1. **컬럼 정의 JSON**: 대장 컬럼 목록을 JSON 배열로 저장하여 유연한 구조 지원.
2. **레이아웃 enum**: 사진대지 배치 방식을 제한된 선택지(2x1, 2x2, 2x3, 3x3)로 제공.
3. **document_type_config 연계**: generate_ledger=true인 유형에만 ledger_config 적용.

## Architecture

### 서버 레이어 구조

```
API Layer (ledger_photo_config_router.py)
  ↓
Service Layer (ledger_photo_config_service.py)
  ↓
Repository Layer (ledger_photo_config_repository.py)
  ↓
Database (ledger_config, photo_board_config 테이블)
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/ledger_photo_config_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/ledger-configs` | GET | 대장 설정 목록 조회 |
| `/api/v1/ledger-configs/{config_id}` | PUT | 대장 설정 수정 |
| `/api/v1/photo-board-config` | GET | 사진대지 설정 조회 |
| `/api/v1/photo-board-config` | PUT | 사진대지 설정 수정 |

#### Service Layer

```python
class LedgerPhotoConfigService:
    async def list_ledger_configs(self, profile_id: int) -> list[LedgerConfig]
    async def update_ledger_config(self, config_id: int, data: LedgerConfigUpdate) -> LedgerConfig
    async def get_photo_board_config(self, profile_id: int) -> PhotoBoardConfig
    async def upsert_photo_board_config(self, profile_id: int, data: PhotoBoardConfigUpdate) -> PhotoBoardConfig
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `LedgerConfigTab` | 대장 설정 탭 |
| `ColumnEditor` | 컬럼 추가/삭제/정렬 편집기 |
| `PhotoBoardConfigTab` | 사진대지 설정 탭 |
| `LayoutPreview` | 레이아웃 미리보기 스케치 |

## Data Models

### SQLAlchemy ORM

```python
class LedgerConfig(Base):
    __tablename__ = "ledger_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("settings_profile.id", ondelete="CASCADE"), nullable=False)
    type_code = Column(Text, nullable=False)
    title = Column(Text, default="")
    columns = Column(Text, default="[]")  # JSON: [{name, width_pct, data_source}]
    sort_columns = Column(Text, default="[]")  # JSON: [{column, order}]
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

class PhotoBoardConfig(Base):
    __tablename__ = "photo_board_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("settings_profile.id", ondelete="CASCADE"), nullable=False, unique=True)
    layout_style = Column(Text, default="2x2")  # 2x1, 2x2, 2x3, 3x3
    caption_style = Column(Text, default="date_desc")  # date_desc, desc_only, date_only, none
    aspect_ratio = Column(Text, default="4:3")  # 4:3, 16:9, 1:1
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
```

### TypeScript 인터페이스

```typescript
interface ColumnDefinition {
  name: string;
  width_pct: number;
  data_source: string;
}

interface LedgerConfig {
  id: number;
  profile_id: number;
  type_code: string;
  title: string;
  columns: ColumnDefinition[];
  sort_columns: { column: string; order: 'asc' | 'desc' }[];
}

interface PhotoBoardConfig {
  id: number;
  profile_id: number;
  layout_style: '2x1' | '2x2' | '2x3' | '3x3';
  caption_style: 'date_desc' | 'desc_only' | 'date_only' | 'none';
  aspect_ratio: '4:3' | '16:9' | '1:1';
}
```

## Correctness Properties

### Property 1: 컬럼 정의 라운드트립
*For any* 유효한 컬럼 정의 배열을 저장 후 조회하면, 동일한 순서와 내용이 반환되어야 한다.

### Property 2: 컬럼 수 제한
*For any* 대장 설정에 컬럼을 추가할 때, 2개 미만 또는 15개 초과는 거부되어야 한다.

### Property 3: 레이아웃 enum 유효성
*For any* layout_style 설정 시, 허용된 값(2x1, 2x2, 2x3, 3x3) 외의 값은 거부되어야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| CONFIG_NOT_FOUND | 404 | 존재하지 않는 설정 ID |
| INVALID_LAYOUT | 422 | 허용되지 않은 레이아웃 값 |
| COLUMN_COUNT_INVALID | 422 | 컬럼 수 범위 초과 |
| INVALID_COLUMN_DEF | 422 | 컬럼 정의 필수 필드 누락 |

## Testing Strategy

- **Property Tests**: 컬럼 정의 라운드트립, 컬럼 수 제한, enum 유효성
- **Unit Tests**: 기본 설정 생성, 컬럼 정렬 로직
- **Integration Tests**: 설정 저장→조회, 프로필 CASCADE 삭제
- **Frontend Tests**: ColumnEditor 드래그&드롭, LayoutPreview 렌더링
