# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "파일 검색" 기능에 대한 요구사항을 정의한다.

파일 검색은 설정된 루트 경로 하위의 모든 파일을 재귀적으로 탐색하고, 날짜 필터링과 확장자 필터링을 적용하여 취합 대상 파일 목록을 생성하는 기능이다.

**연동 관계:**
- **의존**: Spec 04 (folder-config) — 검색 루트 경로
- **의존**: Spec 03 (document-sample) — 지원 확장자 목록
- **제공**: Spec 07 (file-copy)에 검색 결과(파일 경로 목록) 전달

## Glossary

- **Scan_Job**: 1회의 파일 검색 작업 단위
- **Date_Filter**: 날짜 범위 필터 (시작일~종료일)
- **Extension_Filter**: 대상 파일 확장자 필터
- **Scan_Result**: 검색 결과 (파일 경로, 크기, 수정일, 추정 유형)
- **Date_Source**: 날짜 추출 소스 (파일명 패턴, 수정일, EXIF)

## Requirements

### Requirement 1: 재귀 파일 검색

**User Story:** As a CM단 문서 담당자, I want 지정된 폴더의 모든 하위 파일을 검색할 수 있도록, so that 깊은 폴더 구조에 분산된 문서도 빠짐없이 수집할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 스캔을 요청하면, THE System SHALL 설정된 root_path 하위의 모든 파일을 재귀적으로 탐색한다.
2. THE System SHALL 심볼릭 링크를 따르지 않고, 순환 참조를 감지하여 무한 루프를 방지한다.
3. THE System SHALL 검색 진행 상황을 실시간으로 표시한다 (탐색 중인 폴더명, 발견 파일 수).
4. IF root_path가 설정되지 않았거나 존재하지 않으면, THEN THE System SHALL 스캔을 거부하고 경로 설정 안내 메시지를 표시한다.
5. THE System SHALL 접근 권한이 없는 폴더는 스킵하고 로그에 기록한다.

### Requirement 2: 날짜 필터링

**User Story:** As a CM단 문서 담당자, I want 특정 기간의 문서만 검색할 수 있도록, so that 당월 보고서에 필요한 문서만 수집할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 날짜 범위(시작일, 종료일)를 지정하면, THE System SHALL 해당 기간에 해당하는 파일만 결과에 포함한다.
2. THE System SHALL 날짜를 다음 소스에서 추출한다: ① 파일명 내 날짜 패턴 (YYYYMMDD, YYYY-MM-DD, YYMMDD), ② 파일 수정일, ③ 사진 EXIF 촬영일.
3. THE System SHALL 날짜 추출 우선순위를 파일명 > EXIF > 수정일 순으로 적용한다.
4. IF 날짜를 추출할 수 없는 파일이면, THEN THE System SHALL 해당 파일을 '날짜 미상'으로 분류하고 결과에 포함하되 별도 표시한다.
5. WHEN 날짜 필터가 지정되지 않으면, THE System SHALL 모든 파일을 기간 무관하게 포함한다.

### Requirement 3: 확장자 필터링

**User Story:** As a CM단 문서 담당자, I want 특정 확장자의 파일만 검색할 수 있도록, so that 관련 문서 파일만 수집 대상에 포함할 수 있다.

#### Acceptance Criteria

1. WHEN 확장자 필터가 설정되면, THE System SHALL 해당 확장자에 해당하는 파일만 결과에 포함한다.
2. THE System SHALL 기본 확장자 목록을 document_type_config의 supported_extensions 합집합으로 설정한다.
3. THE System SHALL 확장자 비교 시 대소문자를 구분하지 않는다 (.PDF와 .pdf를 동일 취급).
4. IF 확장자 필터가 빈 목록이면, THEN THE System SHALL 모든 확장자의 파일을 포함한다.

### Requirement 4: 검색 결과 제공

**User Story:** As a CM단 문서 담당자, I want 검색 결과를 요약 통계와 함께 확인할 수 있도록, so that 수집 대상을 검토하고 조정할 수 있다.

#### Acceptance Criteria

1. WHEN 검색이 완료되면, THE System SHALL 총 파일 수, 총 크기, 확장자별 통계를 표시한다.
2. THE System SHALL 검색 결과를 파일 경로, 크기, 수정일, 추정 날짜, 확장자 목록으로 반환한다.
3. WHEN 사용자가 검색 결과를 확인하면, THE System SHALL 파일 목록을 페이지네이션으로 표시한다 (기본 100건).
4. THE System SHALL 스캔 작업 ID를 생성하여 결과를 서버에 임시 저장한다.
5. IF 검색 결과가 0건이면, THEN THE System SHALL 조건 변경을 안내하는 메시지를 표시한다.
