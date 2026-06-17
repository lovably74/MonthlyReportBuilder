# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "대장 자동 생성" 기능에 대한 요구사항을 정의한다.

대장 생성은 추출된 데이터를 문서 유형별 대장(목록표) 형식으로 정리하여 테이블 데이터를 생성하는 기능이다. 생성된 대장 데이터는 HWPX 렌더러에 전달되어 최종 보고서에 삽입된다.

**연동 관계:**
- **의존**: Spec 05 (ledger-photo-config) — 대장 타이틀, 컬럼 정의, 정렬 기준
- **의존**: Spec 09 (data-extraction) — 추출된 구조화 데이터
- **제공**: Spec 11 (hwpx-renderer)에 대장 테이블 데이터 전달

## Glossary

- **Ledger**: 문서 유형별 목록표 (대장) 데이터
- **Ledger_Row**: 대장의 1행 데이터 (추출된 레코드 1건에 해당)
- **Ledger_Table**: 완성된 대장 테이블 (헤더 + 데이터 행 배열)

## Requirements

### Requirement 1: 대장 데이터 생성

**User Story:** As a CM단 문서 담당자, I want 추출된 데이터로 대장이 자동 생성되도록, so that 수백 건의 데이터를 수동으로 표에 입력하지 않아도 된다.

#### Acceptance Criteria

1. WHEN 대장 생성이 시작되면, THE System SHALL generate_ledger=true인 문서 유형별로 대장을 생성한다.
2. WHEN 대장을 생성하면, THE System SHALL ledger_config의 컬럼 정의에 따라 extracted_record에서 필드를 매핑한다.
3. THE System SHALL 대장 헤더를 컬럼 정의의 display_name 순서로 생성한다.
4. THE System SHALL 데이터 행을 정렬 설정(sort_columns, sort_order)에 따라 정렬한다.
5. IF 추출 데이터에 매핑할 필드가 없으면, THEN THE System SHALL 해당 셀을 빈 문자열로 채운다.
6. WHEN 대장 생성이 완료되면, THE System SHALL 유형별 대장 행 수를 요약 표시한다.

### Requirement 2: 대장 번호 자동 부여

**User Story:** As a CM단 문서 담당자, I want 대장 행에 순번이 자동으로 부여되도록, so that 번호 매김을 수동으로 하지 않아도 된다.

#### Acceptance Criteria

1. THE System SHALL 대장의 첫 번째 컬럼이 '번호'인 경우 1부터 순차적으로 번호를 자동 부여한다.
2. THE System SHALL 번호 부여 시 정렬 완료 후의 순서를 기준으로 한다.
3. IF 사용자가 행을 수동으로 추가/삭제하면, THEN THE System SHALL 번호를 재부여한다.

### Requirement 3: 대장 데이터 형식 변환

**User Story:** As a CM단 문서 담당자, I want 대장 데이터가 HWPX 삽입에 적합한 형식으로 제공되도록, so that 렌더러가 바로 사용할 수 있다.

#### Acceptance Criteria

1. THE System SHALL 대장 데이터를 JSON 배열 형식(header + rows)으로 출력한다.
2. THE System SHALL 날짜 필드를 'YYYY.MM.DD' 형식으로 통일한다.
3. THE System SHALL 숫자 필드에 천단위 구분자(,)를 적용한다.
4. THE System SHALL 각 셀 데이터의 최대 길이를 100자로 제한하고, 초과 시 말줄임 처리한다.
