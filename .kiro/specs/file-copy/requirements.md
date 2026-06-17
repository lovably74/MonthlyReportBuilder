# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "파일 복사" 기능에 대한 요구사항을 정의한다.

파일 복사는 검색된 파일을 작업폴더로 복사하고, 파일명 충돌 시 자동 처리하며, 복사된 파일 목록을 관리하는 기능이다. 이 단계에서 collection_job이 생성되어 이후 분류·추출 작업의 기준이 된다.

**연동 관계:**
- **의존**: Spec 04 (folder-config) — 작업폴더 경로
- **의존**: Spec 06 (file-scanner) — 검색 결과 파일 목록
- **제공**: Spec 08 (document-classification)에 복사된 파일 목록 전달
- DB: collection_job, collected_file 테이블

## Glossary

- **Collection_Job**: 1회의 취합 작업 단위 (스캔~복사~분류~추출을 아우르는 단위)
- **Collected_File**: 작업폴더로 복사된 개별 파일 레코드
- **Conflict_Resolution**: 동일 파일명 충돌 시 처리 방식 (rename, skip, overwrite)

## Requirements

### Requirement 1: 작업폴더 생성

**User Story:** As a CM단 문서 담당자, I want 취합 작업마다 독립된 작업폴더가 생성되도록, so that 작업 간 파일이 섞이지 않고 관리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 취합을 시작하면, THE System SHALL collection_job 레코드를 생성하고 고유 job_id를 부여한다.
2. WHEN collection_job이 생성되면, THE System SHALL 작업폴더 하위에 `{YYYYMM}_{job_id}/` 디렉토리를 생성한다.
3. IF 작업폴더 경로에 쓰기 권한이 없으면, THEN THE System SHALL 오류를 표시하고 작업을 중단한다.
4. THE System SHALL collection_job에 profile_id, 시작시각, 상태(CREATED, IN_PROGRESS, COMPLETED, FAILED)를 기록한다.

### Requirement 2: 파일 복사 실행

**User Story:** As a CM단 문서 담당자, I want 검색된 파일을 작업폴더로 복사할 수 있도록, so that 원본 파일을 보존하면서 안전하게 작업할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 파일 복사를 시작하면, THE System SHALL scan_result의 모든 파일을 작업폴더로 복사한다.
2. THE System SHALL 복사 진행률(완료 수/전체 수, 퍼센트)을 실시간으로 표시한다.
3. WHEN 파일 복사가 완료되면, THE System SHALL 각 파일에 대해 collected_file 레코드를 생성한다 (원본경로, 복사경로, 파일크기, 복사일시).
4. IF 복사 중 개별 파일 오류가 발생하면, THEN THE System SHALL 해당 파일을 스킵하고 오류 로그에 기록하며 나머지 파일 복사를 계속한다.
5. WHEN 전체 복사가 완료되면, THE System SHALL 성공/실패 건수 요약을 표시한다.

### Requirement 3: 파일명 충돌 처리

**User Story:** As a CM단 문서 담당자, I want 동일 파일명 충돌 시 자동으로 처리되도록, so that 수동 개입 없이 복사가 완료된다.

#### Acceptance Criteria

1. IF 작업폴더에 동일 파일명이 이미 존재하면, THEN THE System SHALL 기본 정책(rename)에 따라 파일명 뒤에 `_N` 접미사를 추가하여 저장한다.
2. THE System SHALL 충돌 처리 정책을 사용자가 설정할 수 있도록 한다 (rename/skip/overwrite).
3. WHEN rename 정책 적용 시, THE System SHALL `파일명_1.확장자`, `파일명_2.확장자` 순으로 순번을 증가시킨다.
4. THE System SHALL 충돌이 발생한 파일의 원본경로와 처리 결과를 로그에 기록한다.

### Requirement 4: 복사 작업 관리

**User Story:** As a CM단 문서 담당자, I want 복사 작업을 중단하거나 재시도할 수 있도록, so that 오류 상황에 유연하게 대응할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 복사 중단을 요청하면, THE System SHALL 현재 파일 복사 완료 후 작업을 중지하고 상태를 FAILED로 변경한다.
2. WHEN 사용자가 실패한 작업의 재시도를 요청하면, THE System SHALL 미복사 파일만 대상으로 복사를 재개한다.
3. THE System SHALL 작업 상태 변경 시 updated_at을 갱신한다.
