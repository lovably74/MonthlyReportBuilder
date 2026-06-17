# Design Document: 작업 이력 및 로그 (history-logs)

## Overview

작업 이력 및 로그는 모든 취합/생성 작업의 이력을 기록하고, 오류 발생 시 상세 로그를 관리하는 기능이다. 중앙 app_log 테이블에 통합 로깅하며 90일 자동 정리 정책을 적용한다.

### 핵심 설계 결정

1. **통합 로그 테이블**: 작업 이력과 오류 로그를 app_log 단일 테이블로 관리.
2. **log_level 분류**: INFO (작업 이력), WARNING, ERROR, CRITICAL (오류 로그).
3. **90일 보관**: 스케줄러로 90일 초과 로그 자동 삭제.
4. **내보내기 지원**: JSON/CSV 파일로 기간별 로그 내보내기.

## Architecture

### 로깅 구조

```
모든 Service 모듈
  → AppLogger.log(level, source, message, job_id, detail)
    → app_log INSERT
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/history_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/logs` | GET | 로그 목록 조회 (필터/페이지네이션) |
| `/api/v1/logs/summary` | GET | 최근 24시간 요약 통계 |
| `/api/v1/logs/export` | POST | 로그 내보내기 |
| `/api/v1/logs/cleanup` | POST | 수동 정리 실행 |

#### Service Layer

```python
class HistoryLogService:
    async def list_logs(self, filters: LogFilter) -> LogListResponse
    async def get_summary(self) -> LogSummary
    async def export_logs(self, start_date: str, end_date: str, format: str) -> str
    async def cleanup_old_logs(self, retention_days: int = 90) -> int

class AppLogger:
    async def info(self, source: str, message: str, job_id: int = None)
    async def warning(self, source: str, message: str, job_id: int = None, detail: str = None)
    async def error(self, source: str, message: str, job_id: int = None, detail: str = None)
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `HistoryPage` | 이력/로그 메인 페이지 |
| `LogTable` | 로그 목록 테이블 (필터, 페이지네이션) |
| `LogDetailDialog` | 로그 상세 보기 대화상자 |
| `LogSummaryCard` | 최근 24시간 요약 카드 |
| `LogExportDialog` | 내보내기 설정 대화상자 |

## Data Models

### SQLAlchemy ORM

```python
class AppLog(Base):
    __tablename__ = "app_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Text, nullable=False)
    log_level = Column(Text, nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    log_source = Column(Text, nullable=False)  # scanner, copier, classifier, extractor, renderer, etc.
    message = Column(Text, nullable=False)
    job_id = Column(Integer, ForeignKey("collection_job.id", ondelete="SET NULL"))
    detail = Column(Text)  # stack trace or extra info
    file_path = Column(Text)  # 관련 파일 경로
```

### TypeScript 인터페이스

```typescript
interface AppLog {
  id: number;
  timestamp: string;
  log_level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  log_source: string;
  message: string;
  job_id: number | null;
  detail: string | null;
}

interface LogSummary {
  total_24h: number;
  info_count: number;
  warning_count: number;
  error_count: number;
  critical_count: number;
}
```

## Correctness Properties

### Property 1: 로그 시간순 보장
*For any* 로그 목록 조회 시, timestamp는 단조 감소(최신 우선) 순서여야 한다.

### Property 2: 90일 정리 정확성
*For any* cleanup 실행 후, retention_days일 이전의 로그는 존재하지 않아야 한다.

### Property 3: 내보내기 완전성
*For any* 기간 내 로그를 내보내면, 내보낸 건수 = 해당 기간 DB 레코드 수여야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| INVALID_DATE_RANGE | 422 | 잘못된 날짜 범위 |
| EXPORT_FAILED | 500 | 내보내기 파일 생성 실패 |
| LOG_NOT_FOUND | 404 | 존재하지 않는 로그 ID |

## Testing Strategy

- **Property Tests**: 시간순 정렬, 90일 정리, 내보내기 완전성
- **Unit Tests**: AppLogger 동작, 날짜 필터 파싱
- **Integration Tests**: 로그 기록→조회→내보내기 플로우, 정리 스케줄
- **Frontend Tests**: LogTable 필터, LogDetailDialog 렌더링
