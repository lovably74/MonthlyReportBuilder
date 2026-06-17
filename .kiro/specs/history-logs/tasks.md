# Implementation Plan: 작업 이력 및 로그 (history-logs)

## Overview

모든 취합/생성 작업의 이력을 기록하고 오류 로그를 관리하는 기능을 구현한다. app_log 테이블에 통합 로깅하며, 90일 자동 정리 정책과 로그 내보내기를 지원한다.

## Tasks

- [ ] 1. 데이터 모델 및 로깅 인프라
  - [ ] 1.1 app_log 테이블 생성
    - `app/models/app_log.py`에 ORM 모델 정의
    - 인덱스: (timestamp DESC), (log_level), (job_id)
  - [ ] 1.2 AppLogger 유틸리티 구현
    - `app/core/app_logger.py`
    - info, warning, error 메서드
    - 모든 Service에서 주입하여 사용

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 HistoryLogService 구현
    - list_logs: 필터(level, source, job_id, date) + 페이지네이션
    - get_summary: 최근 24시간 통계
    - export_logs: JSON/CSV 내보내기
    - cleanup_old_logs: 90일 초과 삭제
  - [ ] 2.2 History API Router
    - GET /api/v1/logs (필터 + 페이지네이션)
    - GET /api/v1/logs/summary
    - POST /api/v1/logs/export
    - POST /api/v1/logs/cleanup

- [ ] 3. 스케줄러 설정
  - [ ] 3.1 90일 자동 정리 스케줄러
    - 매일 자정 실행 (APScheduler 또는 asyncio 기반)

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 HistoryPage + LogTable
    - 필터 (레벨, 소스, 날짜 범위), 페이지네이션
  - [ ] 4.2 LogDetailDialog + LogSummaryCard
  - [ ] 4.3 LogExportDialog
    - 기간 선택 + 형식 선택(JSON/CSV)
  - [ ] 4.4 API Client 및 Store

- [ ] 5. 기존 Service에 로깅 통합
  - [ ] 5.1 FileCopyService, ClassificationService, ExtractionService 등에 AppLogger 주입
    - 작업 시작/완료/실패 시 자동 로그 기록

- [ ] 6. 테스트
  - [ ] 6.1 Property Tests: 시간순 정렬, 90일 정리, 내보내기 완전성
  - [ ] 6.2 Unit Tests: AppLogger 동작, 날짜 필터
  - [ ] 6.3 Integration Tests: 로그 기록→조회→내보내기→정리

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["6.1", "6.2", "6.3"] }
  ]
}
```

## Notes

- AppLogger는 의존성 주입으로 모든 Service에서 사용
- 로그 내보내기 시 민감 정보(사용자명 포함 경로) 마스킹 옵션
- 프론트엔드에서 별도 탭 또는 페이지로 구성 (환경설정 외부)
