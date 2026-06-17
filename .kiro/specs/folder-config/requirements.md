# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "작업폴더 설정" 기능에 대한 요구사항을 정의한다.

작업폴더 설정은 파일 검색의 루트 경로, 작업 결과물의 저장 위치, 생성되는 파일의 명명 규칙을 관리하는 기능이다.

**연동 관계:**
- **의존**: Spec 01 (settings-profile) — `folder_config.profile_id` FK로 프로필에 종속
- **제공**: Spec 06 (file-scanner)에 검색 루트 경로 제공
- **제공**: Spec 07 (file-copy)에 작업폴더 생성 경로 제공
- **제공**: Spec 15 (report-output)에 결과물 저장 경로 및 파일명 규칙 제공

## Glossary

- **Root_Path**: 문서 파일 검색을 시작하는 최상위 디렉토리 경로
- **Work_Folder_Path**: 취합 작업 시 파일을 복사·정리하는 작업 디렉토리 경로
- **Output_Path**: 최종 결과물(보고서, 대장)이 저장되는 디렉토리 경로
- **Naming_Rule**: 결과 파일명 생성 규칙 (변수 치환 패턴)
- **Folder_Config**: 프로필별 폴더 설정 레코드

## Requirements

### Requirement 1: 검색 루트 경로 설정

**User Story:** As a CM단 문서 담당자, I want 파일 검색의 시작 경로를 지정할 수 있도록, so that 관련 문서가 저장된 폴더만 검색 대상으로 삼을 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 루트 경로 설정을 요청하면, THE System SHALL 폴더 선택 대화상자를 표시하고 선택된 경로를 저장한다.
2. WHEN 경로가 설정되면, THE System SHALL 해당 경로의 존재 여부와 읽기 권한을 검증한다.
3. IF 설정된 경로가 존재하지 않거나 읽기 권한이 없으면, THEN THE System SHALL 경고 메시지를 표시하고 저장을 허용하되 경고 아이콘을 표시한다.
4. THE System SHALL 경로를 절대 경로로 정규화하여 저장한다.
5. WHEN 루트 경로가 변경되면, THE System SHALL updated_at을 갱신한다.

### Requirement 2: 작업폴더 경로 설정

**User Story:** As a CM단 문서 담당자, I want 작업폴더의 위치를 지정할 수 있도록, so that 취합 작업 중 파일이 정리되는 위치를 제어할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 작업폴더 경로를 설정하면, THE System SHALL 폴더 선택 대화상자를 통해 경로를 지정하고 저장한다.
2. THE System SHALL 작업폴더 경로의 쓰기 권한을 검증한다.
3. IF 쓰기 권한이 없으면, THEN THE System SHALL 오류 메시지를 표시하고 경로 저장을 거부한다.
4. WHEN 작업폴더 하위 구조 패턴을 설정하면, THE System SHALL `{YYYY}/{MM}/` 또는 `{YYYYMM}/` 등의 변수 패턴을 지원한다.

### Requirement 3: 결과물 저장 경로 및 파일명 규칙

**User Story:** As a CM단 문서 담당자, I want 결과 파일의 저장 위치와 파일명 규칙을 설정할 수 있도록, so that 발주처 요구 형식에 맞게 산출물을 관리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 출력 경로를 설정하면, THE System SHALL 폴더 선택 대화상자를 통해 경로를 지정한다.
2. WHEN 사용자가 파일명 규칙을 설정하면, THE System SHALL `{PROJECT}_{YYYYMM}_월간보고서.hwpx` 등의 변수 치환 패턴을 저장한다.
3. THE System SHALL 파일명 규칙에 사용 가능한 변수 목록({PROJECT}, {YYYY}, {MM}, {ROUND}, {DATE})을 안내한다.
4. IF 파일명 규칙에 파일시스템 금지 문자가 포함되면, THEN THE System SHALL 유효하지 않은 패턴임을 나타내는 오류를 표시한다.
5. THE System SHALL 설정된 파일명 규칙의 미리보기(예시 결과)를 실시간으로 표시한다.

### Requirement 4: 폴더 설정 검증

**User Story:** As a CM단 문서 담당자, I want 설정된 경로들이 유효한지 한눈에 확인할 수 있도록, so that 작업 실행 전 문제를 사전에 파악할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 폴더 설정 탭을 열면, THE System SHALL 각 경로의 존재 여부와 권한 상태를 아이콘으로 표시한다.
2. WHEN 사용자가 '경로 검증' 버튼을 클릭하면, THE System SHALL 모든 설정 경로를 재검증하고 결과를 갱신한다.
3. IF 필수 경로(root_path, work_folder_path)가 미설정이면, THEN THE System SHALL 설정 필요 안내 메시지를 표시한다.
