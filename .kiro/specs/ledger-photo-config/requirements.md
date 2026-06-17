# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "대장/사진대지 설정" 기능에 대한 요구사항을 정의한다.

대장 설정은 문서 유형별 대장의 타이틀, 컬럼 구성, 정렬 기준을 관리하고, 사진대지 설정은 1페이지당 사진 배치 수, 캡션 표기 방식, 레이아웃 스타일을 관리하는 기능이다.

**연동 관계:**
- **의존**: Spec 01 (settings-profile) — `ledger_config.profile_id` FK
- **의존**: Spec 03 (document-sample) — `document_type_config`과 연계하여 대장 생성 대상 결정
- **제공**: Spec 10 (ledger-generation)에 대장 컬럼/타이틀 설정값 제공
- **제공**: Spec 12 (photo-board)에 사진대지 배열/캡션 설정값 제공

## Glossary

- **Ledger_Config**: 문서 유형별 대장 생성 설정 (타이틀, 컬럼 정의, 정렬)
- **Photo_Board_Config**: 사진대지 레이아웃 설정
- **Column_Definition**: 대장 컬럼 정의 (이름, 너비비율, 데이터소스)
- **Layout_Style**: 사진대지 페이지 배치 방식 (2x2, 2x3, 3x3 등)

## Requirements

### Requirement 1: 대장 타이틀 및 컬럼 설정

**User Story:** As a CM단 문서 담당자, I want 문서 유형별 대장의 타이틀과 컬럼을 설정할 수 있도록, so that 발주처 양식에 맞는 대장을 자동 생성할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 대장 설정 탭을 열면, THE System SHALL generate_ledger=true인 문서 유형 목록을 표시한다.
2. WHEN 사용자가 특정 문서 유형의 대장 타이틀을 입력하면, THE System SHALL 최대 100자의 텍스트를 저장한다.
3. WHEN 사용자가 컬럼을 추가하면, THE System SHALL 컬럼명, 너비비율(%), 데이터소스 필드를 입력받아 저장한다.
4. THE System SHALL 컬럼 순서를 드래그&드롭으로 변경할 수 있도록 지원한다.
5. THE System SHALL 문서 유형별 최소 2개, 최대 15개의 컬럼을 허용한다.
6. IF 컬럼 너비비율의 합이 100%가 아니면, THEN THE System SHALL 경고를 표시하되 저장은 허용한다.

### Requirement 2: 대장 정렬 및 그룹핑 설정

**User Story:** As a CM단 문서 담당자, I want 대장 데이터의 정렬 기준을 설정할 수 있도록, so that 보고서 내 대장이 일관된 순서로 표시된다.

#### Acceptance Criteria

1. WHEN 사용자가 정렬 기준 컬럼을 선택하면, THE System SHALL 해당 컬럼 기준으로 오름차순/내림차순을 설정하고 저장한다.
2. THE System SHALL 최대 3개의 정렬 기준 컬럼을 우선순위 순으로 지원한다.
3. THE System SHALL 날짜 컬럼 기본 정렬을 오름차순(과거→최근)으로 설정한다.

### Requirement 3: 사진대지 레이아웃 설정

**User Story:** As a CM단 문서 담당자, I want 사진대지의 페이지 배치를 설정할 수 있도록, so that 현장 요구에 맞는 사진대지를 생성할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 사진대지 레이아웃을 설정하면, THE System SHALL 1페이지당 사진 수(2, 4, 6, 9장)를 선택할 수 있도록 한다.
2. WHEN 사용자가 배치 방식을 선택하면, THE System SHALL 2x1, 2x2, 2x3, 3x3 중 하나를 저장한다.
3. WHEN 사용자가 캡션 표기 방식을 설정하면, THE System SHALL '촬영일자+설명', '설명만', '일자만', '없음' 중 선택값을 저장한다.
4. THE System SHALL 사진대지 설정의 미리보기(레이아웃 스케치)를 표시한다.
5. WHEN 사용자가 사진 크기 비율을 설정하면, THE System SHALL 가로:세로 비율(4:3, 16:9, 1:1)을 저장한다.
