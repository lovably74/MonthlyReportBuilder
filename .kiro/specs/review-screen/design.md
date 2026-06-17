# Design Document: 검토·수정 화면 (review-screen)

## Overview

검토·수정 화면은 대장, 요약문, 사진대지를 통합적으로 검토하고 편집할 수 있는 클라이언트 중심 UI 기능이다. 서버 API를 통해 데이터를 조회/수정하며, 최종 확정 시 REVIEWED 상태로 전환된다.

### 핵심 설계 결정

1. **탭 구조**: 대장/요약문/사진대지를 독립 탭으로 구분.
2. **인라인 편집**: 대장은 셀 직접 편집, 요약문은 텍스트 에디터.
3. **자동 저장**: 요약문은 5초 debounce auto-save.
4. **확정 상태 관리**: REVIEWED 상태 전환 및 해제 지원.

## Architecture

### 클라이언트 구조

```
ReviewPage
  ├── LedgerReviewTab (대장 편집 테이블)
  ├── SummaryReviewTab (요약문 에디터)
  └── PhotoBoardReviewTab (사진대지 미리보기/편집)
```

## Components and Interfaces

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `ReviewPage` | 검토 화면 메인 페이지 |
| `LedgerReviewTab` | 대장 편집 테이블 탭 |
| `EditableTable` | 인라인 편집 가능한 테이블 |
| `SummaryReviewTab` | 요약문 편집 탭 |
| `MarkdownEditor` | 간단한 마크다운 에디터 |
| `PhotoBoardReviewTab` | 사진대지 검토 탭 |
| `PhotoGrid` | 사진 배치 미리보기 + 드래그 정렬 |
| `FinalizeButton` | 최종 확정 버튼 |

### Backend API (기존 엔드포인트 활용)

| 용도 | Endpoint | Spec |
|------|----------|------|
| 대장 조회/수정 | `/api/v1/jobs/{job_id}/ledgers` | Spec 10 |
| 요약문 조회/수정 | `/api/v1/jobs/{job_id}/summary` | Spec 13 |
| 사진대지 조회 | `/api/v1/jobs/{job_id}/photo-board` | Spec 12 |
| 상태 변경 | `/api/v1/jobs/{job_id}/finalize` | 본 Spec |

#### 추가 엔드포인트

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/finalize` | POST | 최종 확정 |
| `/api/v1/jobs/{job_id}/unfinalize` | POST | 확정 해제 |

## Data Models

### Zustand Store

```typescript
interface ReviewStore {
  currentJobId: number | null;
  activeTab: 'ledger' | 'summary' | 'photo';
  isFinalized: boolean;
  modifiedCells: Set<string>;
  
  setActiveTab: (tab: string) => void;
  finalize: (jobId: number) => Promise<void>;
  unfinalize: (jobId: number) => Promise<void>;
}
```

## Correctness Properties

### Property 1: 확정 전제 조건
*For any* 확정 요청 시, collection_job의 상태가 EXTRACTED 이상이어야 한다.

### Property 2: 수정 추적 무결성
*For any* 인라인 편집 후, 수정된 셀은 원본 값과 현재 값을 모두 보유해야 한다.

### Property 3: 자동 저장 일관성
*For any* auto-save 수행 시, 서버에 저장된 값과 클라이언트 UI의 값이 일치해야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| JOB_NOT_READY | 400 | 확정 가능한 상태가 아님 |
| SAVE_CONFLICT | 409 | 동시 수정 충돌 |
| INCOMPLETE_REVIEW | 400 | 미검토 항목 존재 |

## Testing Strategy

- **Unit Tests**: EditableTable 셀 편집, MarkdownEditor 서식
- **Integration Tests**: 확정/해제 플로우, auto-save 동작
- **Frontend Tests**: 탭 전환, 드래그&드롭, 수정 표시
