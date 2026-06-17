# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "HWPX 생성 엔진" 기능에 대한 요구사항을 정의한다.

HWPX 렌더러는 등록된 템플릿 HWPX 파일을 복사한 뒤, 내부 XML의 태그를 실제 데이터로 치환하고, 표와 이미지를 삽입하여 최종 월간보고서 HWPX 파일을 생성하는 핵심 엔진이다.

**연동 관계:**
- **의존**: Spec 02 (template-registration) — 템플릿 HWPX 파일 및 태그 위치
- **의존**: Spec 10 (ledger-generation) — 대장 테이블 데이터
- **의존**: Spec 12 (photo-board) — 사진대지 이미지/데이터
- **의존**: Spec 13 (ai-summary) — AI 요약문 텍스트
- **제공**: 최종 HWPX 파일 생성 → Spec 15 (report-output)에 전달

## Glossary

- **Tag_Replacement**: 템플릿 XML 내 태그를 실제 값으로 치환하는 작업
- **Table_Insertion**: 태그 위치에 대장 데이터를 표로 삽입하는 작업
- **Image_Insertion**: 태그 위치에 이미지를 삽입하고 BinData에 추가하는 작업
- **BinData**: HWPX ZIP 내부의 이미지/바이너리 파일 저장 디렉토리
- **Manifest**: HWPX ZIP 내부 리소스 목록 관리 파일

## Requirements

### Requirement 1: 텍스트 태그 치환

**User Story:** As a CM단 문서 담당자, I want 템플릿의 태그가 실제 데이터로 자동 치환되도록, so that 수동 편집 없이 보고서가 완성된다.

#### Acceptance Criteria

1. WHEN 렌더링이 시작되면, THE System SHALL 템플릿 HWPX 파일을 작업 디렉토리에 복사한다.
2. WHEN 복사된 HWPX를 ZIP 해제하면, THE System SHALL Contents/section*.xml 파일들을 순회하며 태그를 탐색한다.
3. WHEN 텍스트 태그(PROJECT_NAME, WRITE_YYMM, REPORT_ROUND 등)를 발견하면, THE System SHALL 해당 태그를 입력된 데이터 값으로 치환한다.
4. IF 태그에 매핑된 데이터가 없으면, THEN THE System SHALL 해당 태그를 빈 문자열로 치환하고 경고 로그를 기록한다.
5. THE System SHALL 치환 시 XML 특수문자(<, >, &, ", ')를 적절히 이스케이프한다.

### Requirement 2: 표 삽입

**User Story:** As a CM단 문서 담당자, I want 대장 데이터가 보고서의 표로 자동 삽입되도록, so that 대장을 별도로 작성할 필요가 없다.

#### Acceptance Criteria

1. WHEN 표 태그(TFA_LIST, IRR_LIST 등)를 발견하면, THE System SHALL 해당 위치에 대장 데이터를 HWPX 표 XML로 변환하여 삽입한다.
2. THE System SHALL 표의 열 수와 너비를 ledger_config의 컬럼 정의에 따라 설정한다.
3. THE System SHALL 표 헤더 행과 데이터 행을 구분하여 스타일을 적용한다.
4. IF 대장 데이터가 비어있으면, THEN THE System SHALL '해당 없음' 텍스트가 포함된 1행 표를 삽입한다.
5. THE System SHALL 표 행 수가 페이지를 초과할 경우 자동 페이지 분할을 지원한다.

### Requirement 3: 이미지 삽입

**User Story:** As a CM단 문서 담당자, I want 사진대지 이미지가 보고서에 자동 삽입되도록, so that 사진을 하나씩 붙이는 작업이 불필요하다.

#### Acceptance Criteria

1. WHEN 이미지 태그(PHOTO_SITE_VIEW, PHOTO_PROGRESS 등)를 발견하면, THE System SHALL 사진대지 이미지를 해당 위치에 삽입한다.
2. WHEN 이미지를 삽입하면, THE System SHALL BinData/ 디렉토리에 이미지 파일을 추가한다.
3. WHEN 이미지를 삽입하면, THE System SHALL manifest XML에 새 리소스 항목을 등록한다.
4. THE System SHALL 이미지 크기를 태그 위치의 영역에 맞게 자동 조절한다.
5. IF 이미지 파일이 존재하지 않으면, THEN THE System SHALL 플레이스홀더를 삽입하고 경고 로그를 기록한다.

### Requirement 4: HWPX 재압축 및 무결성 검증

**User Story:** As a CM단 문서 담당자, I want 생성된 HWPX 파일이 한글 프로그램에서 정상적으로 열리도록, so that 결과물의 호환성이 보장된다.

#### Acceptance Criteria

1. WHEN 모든 태그 치환과 삽입이 완료되면, THE System SHALL 수정된 파일들을 ZIP으로 재압축하여 HWPX 파일을 생성한다.
2. THE System SHALL ZIP 압축 시 원본 HWPX의 디렉토리 구조를 유지한다.
3. THE System SHALL 생성된 HWPX의 XML 유효성(well-formed)을 검증한다.
4. IF XML 유효성 검증에 실패하면, THEN THE System SHALL 생성을 중단하고 오류 위치를 포함한 메시지를 표시한다.
5. THE System SHALL 생성된 HWPX 파일 경로를 반환한다.
