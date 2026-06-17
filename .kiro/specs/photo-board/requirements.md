# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "사진대지 생성" 기능에 대한 요구사항을 정의한다.

사진대지 생성은 수집된 사진 파일을 설정된 레이아웃에 맞게 배치하고, 캡션을 추가하여 사진대지 이미지/데이터를 생성하는 기능이다.

**연동 관계:**
- **의존**: Spec 05 (ledger-photo-config) — 사진대지 레이아웃/캡션 설정
- **의존**: Spec 09 (data-extraction) — 사진 파일 경로 및 EXIF 데이터
- **제공**: Spec 11 (hwpx-renderer)에 사진대지 이미지/표 데이터 전달

## Glossary

- **Photo_Board_Page**: 사진대지 1페이지 (N장 사진 + 캡션)
- **Photo_Slot**: 1장의 사진이 배치되는 영역
- **Caption**: 사진 하단에 표시되는 설명 텍스트

## Requirements

### Requirement 1: 사진 배치

**User Story:** As a CM단 문서 담당자, I want 사진이 설정된 레이아웃으로 자동 배치되도록, so that 사진대지를 수동으로 만들지 않아도 된다.

#### Acceptance Criteria

1. WHEN 사진대지 생성이 시작되면, THE System SHALL 사진 파일 목록을 촬영일시 순으로 정렬한다.
2. THE System SHALL photo_board_config의 layout_style(2x1, 2x2, 2x3, 3x3)에 따라 페이지당 사진 수를 결정한다.
3. WHEN 사진을 배치하면, THE System SHALL 설정된 가로:세로 비율에 맞게 이미지를 크롭/리사이즈한다.
4. THE System SHALL 사진 수 / 페이지당 배치 수 = 필요 페이지 수로 페이지를 자동 생성한다.
5. IF 사진이 없으면, THEN THE System SHALL 사진대지를 생성하지 않고 해당 태그를 빈 상태로 남긴다.

### Requirement 2: 캡션 생성

**User Story:** As a CM단 문서 담당자, I want 사진에 촬영일자와 설명이 자동으로 표시되도록, so that 사진의 맥락을 파악할 수 있다.

#### Acceptance Criteria

1. WHEN caption_style이 '촬영일자+설명'이면, THE System SHALL "{YYYY.MM.DD} - {description}" 형식으로 캡션을 생성한다.
2. WHEN caption_style이 '설명만'이면, THE System SHALL description만 캡션으로 사용한다.
3. WHEN caption_style이 '일자만'이면, THE System SHALL 촬영일자만 캡션으로 사용한다.
4. WHEN caption_style이 '없음'이면, THE System SHALL 캡션 영역을 생략한다.
5. IF 사진의 description이 없으면, THEN THE System SHALL 파일명에서 설명을 추출하거나 '설명 없음'으로 표시한다.
6. THE System SHALL 캡션 텍스트 길이를 최대 50자로 제한하고 초과 시 말줄임 처리한다.

### Requirement 3: 사진대지 출력 형식

**User Story:** As a CM단 문서 담당자, I want 사진대지가 HWPX에 삽입 가능한 형식으로 출력되도록, so that 렌더러가 바로 사용할 수 있다.

#### Acceptance Criteria

1. THE System SHALL 사진대지를 페이지별 이미지(PNG) + 메타데이터(JSON)로 출력한다.
2. THE System SHALL 출력 이미지 해상도를 A4 인쇄 기준(300 DPI)으로 생성한다.
3. THE System SHALL 메타데이터에 페이지 번호, 사진 수, 캡션 목록을 포함한다.
4. WHEN 사진대지 생성이 완료되면, THE System SHALL 총 페이지 수와 총 사진 수를 요약 반환한다.
