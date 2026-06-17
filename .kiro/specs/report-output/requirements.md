# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "최종 결과 파일 생성" 기능에 대한 요구사항을 정의한다.

최종 결과 생성은 렌더링된 HWPX 보고서, Excel 대장 파일, 검증 리포트를 설정된 경로에 저장하고, 생성 결과를 검증하는 기능이다.

**연동 관계:**
- **의존**: Spec 11 (hwpx-renderer) — 생성된 HWPX 파일
- **의존**: Spec 04 (folder-config) — 저장 경로 및 파일명 규칙
- **제공**: 최종 산출물 (HWPX 보고서, Excel 대장, 검증 리포트)
- DB: report_generation 테이블

## Glossary

- **Report_Package**: 최종 산출물 묶음 (HWPX + Excel + 검증 리포트)
- **Verification_Report**: 생성된 파일의 완전성 검증 결과 보고서
- **Report_Generation**: 1회의 보고서 생성 작업 레코드

## Requirements

### Requirement 1: 결과 파일 저장

**User Story:** As a CM단 문서 담당자, I want 최종 보고서와 대장이 지정된 경로에 자동 저장되도록, so that 결과물을 별도로 정리하지 않아도 된다.

#### Acceptance Criteria

1. WHEN 보고서 생성이 완료되면, THE System SHALL folder_config의 output_path에 결과 파일을 저장한다.
2. THE System SHALL 파일명을 naming_rule에 따라 변수 치환하여 생성한다.
3. THE System SHALL HWPX 보고서, Excel 대장, 검증 리포트를 각각 별도 파일로 저장한다.
4. IF 동일 파일명이 이미 존재하면, THEN THE System SHALL `_v{N}` 접미사를 추가하여 기존 파일을 보존한다.
5. WHEN 저장이 완료되면, THE System SHALL report_generation 테이블에 생성 결과를 기록한다.
6. IF 저장 경로에 쓰기 권한이 없으면, THEN THE System SHALL 오류를 표시하고 다른 경로 선택을 안내한다.

### Requirement 2: Excel 대장 생성

**User Story:** As a CM단 문서 담당자, I want 대장을 Excel 파일로도 받을 수 있도록, so that 별도 편집이나 제출에 활용할 수 있다.

#### Acceptance Criteria

1. THE System SHALL 문서 유형별 대장을 Excel 워크시트(openpyxl)로 생성한다.
2. THE System SHALL 각 문서 유형을 별도 시트에 배치한다.
3. THE System SHALL 헤더 행에 굵은 글꼴과 배경색을 적용한다.
4. THE System SHALL 열 너비를 ledger_config의 컬럼 너비비율에 따라 설정한다.

### Requirement 3: 검증 리포트 생성

**User Story:** As a CM단 문서 담당자, I want 생성 결과의 완전성을 검증한 리포트를 확인할 수 있도록, so that 누락된 항목을 파악할 수 있다.

#### Acceptance Criteria

1. WHEN 보고서 생성 완료 후, THE System SHALL 검증 리포트를 자동 생성한다.
2. THE System SHALL 다음 항목을 검증한다: 태그 치환 완료 여부, 빈 대장 존재 여부, 이미지 삽입 성공 여부, 요약문 존재 여부.
3. THE System SHALL 검증 결과를 '정상', '경고', '오류' 3단계로 분류한다.
4. THE System SHALL 검증 리포트를 텍스트 파일 형식으로 결과 폴더에 저장한다.
5. WHEN 오류 항목이 존재하면, THE System SHALL 사용자에게 경고 대화상자를 표시한다.
