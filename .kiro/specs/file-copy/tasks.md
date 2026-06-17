# Implementation Plan: 파일 복사 (file-copy)

## Overview

검색된 파일을 작업폴더로 복사하고 collection_job/collected_file 레코드를 관리하는 기능을 구현한다. 충돌 처리 정책(rename/skip/overwrite)을 지원하며 복사 진행률을 실시간 제공한다.

## Tasks

- [ ] 1. 데이터 모델 및 마이그레이션
  - [ ] 1.1 collection_job 테이블 생성
    - `app/models/collection_job.py`에 ORM 모델 정의
    - 상태 enum: CREATED, SCANNING, COPIED, CLASSIFIED, EXTRACTED, REVIEWED, COMPLETED, FAILED
  - [ ] 1.2 collected_file 테이블 생성
    - `app/models/collected_file.py`에 ORM 모델 정의
    - FK: job_id → collection_job.id (CASCADE)
  - [ ] 1.3 Pydantic 스키마 정의

- [ ] 2. Service 구현
  - [ ] 2.1 WorkFolderManager 구현
    - create_folder: 패턴 기반 디렉토리 생성
    - resolve_conflict: rename(_1, _2...), skip, overwrite 정책
  - [ ] 2.2 FileCopyService 구현
    - create_job, start_copy, get_job_status, retry_failed
    - 개별 파일 실패 시 스킵 & 로그 기록

- [ ] 3. API Router 구현
  - [ ] 3.1 Collection Job API
    - POST /api/v1/jobs (job 생성)
    - GET /api/v1/jobs/{job_id} (상태 조회)
    - POST /api/v1/jobs/{job_id}/copy (복사 시작)
    - GET /api/v1/jobs/{job_id}/files (복사된 파일 목록)

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 CopyPanel + CopyProgress 컴포넌트
  - [ ] 4.2 CopyResultSummary + ConflictPolicySelect
  - [ ] 4.3 API Client 및 Store

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 복사 완전성, 충돌 처리 고유성, 상태 전이
  - [ ] 5.2 Unit Tests: resolve_conflict 로직, 폴더 패턴 생성
  - [ ] 5.3 Integration Tests: 전체 복사 플로우, 재시도

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- collection_job은 전체 파이프라인(스캔~생성)을 추적하는 핵심 엔터티
- collected_file에 이후 분류(classified_type) 및 추출 결과가 추가됨
- 작업폴더 패턴 예: {YYYYMM}_{job_id}/ → "202401_15/"
