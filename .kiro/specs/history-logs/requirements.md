# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "작업 이력 및 로그" 기능에 대한 요구사항을 정의한다.

작업 이력은 모든 취합/생성 작업의 실행 이력을 기록하고, 오류 발생 시 상세 로그를 관리하여 문제 진단과 작업 추적을 지원하는 기능이다.

**연동 관계:**
- **의존**: 모든 Spec의 작업 결과 (collection_job 상태 변경, 오류 발생 이벤트)
- DB: app_log 테이블

## Glossary

- **App_Log**: 애플리케이션 로그 레코드 (작업 이력 + 오류 로그 통합)
- **Log_Level**: 로그 심각도 (INFO, WARNING, ERROR, CRITICAL)
- **Log_Source**: 로그 발생 모듈 (scanner, copier, classifier, extractor, renderer, etc.)

## Requirements

### Requirement 1: 작업 이력 기록

**User Story:** As a CM단 문서 담당자, I want 모든 취합 작업의 이력을 확인할 수 있도록, so that 과거 작업을 추적하고 재수행할 수 있다.

#### Acceptance Criteria

1. THE System SHALL 모든 collection_job의 생성, 상태 변경, 완료를 app_log에 기록한다.
2. THE System SHALL 각 로그에 timestamp, job_id, log_level, log_source, message를 포함한다.
3. WHEN 사용자가 이력 화면을 열면, THE System SHALL 작업 목록을 최신순으로 표시한다.
4. THE System SHALL 작업별로 소요 시간, 처리 파일 수, 결과 상태를 표시한다.
5. THE System SHALL 로그를 최대 90일간 보관하고, 이후 자동 삭제한다.

### Requirement 2: 오류 로그 관리

**User Story:** As a 시스템 관리자, I want 오류 발생 시 상세 로그를 확인할 수 있도록, so that 문제 원인을 빠르게 파악하고 해결할 수 있다.

#### Acceptance Criteria

1. WHEN 오류가 발생하면, THE System SHALL log_level=ERROR로 상세 오류 정보(스택 트레이스, 파일 경로, 오류 유형)를 기록한다.
2. THE System SHALL 오류 로그를 별도 필터로 조회할 수 있도록 한다.
3. THE System SHALL 최근 24시간 내 ERROR/CRITICAL 수를 대시보드에 표시한다.
4. WHEN 사용자가 특정 오류 로그를 클릭하면, THE System SHALL 상세 정보(스택 트레이스, 관련 파일 경로)를 표시한다.

### Requirement 3: 로그 내보내기

**User Story:** As a 시스템 관리자, I want 로그를 파일로 내보낼 수 있도록, so that 지원 요청 시 로그를 첨부할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 로그 내보내기를 요청하면, THE System SHALL 선택된 기간의 로그를 JSON 또는 CSV 파일로 내보낸다.
2. THE System SHALL 내보내기 시 기간 범위(시작일~종료일)를 지정할 수 있도록 한다.
3. THE System SHALL 내보내기 파일에 민감 정보(경로의 사용자명 등)를 마스킹할 수 있는 옵션을 제공한다.
