# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "검토·수정 화면" 기능에 대한 요구사항을 정의한다.

검토 화면은 자동 생성된 대장, 요약문, 사진대지를 사용자가 최종 확인하고 수정할 수 있는 통합 편집 화면이다. 이 단계에서 최종 확정된 데이터가 보고서 생성에 사용된다.

**연동 관계:**
- **의존**: Spec 09 (data-extraction) — 추출 결과
- **의존**: Spec 10 (ledger-generation) — 대장 데이터
- **의존**: Spec 12 (photo-board) — 사진대지 데이터
- **의존**: Spec 13 (ai-summary) — AI 요약문
- **제공**: Spec 15 (report-output)에 최종 확정 데이터 전달

## Glossary

- **Review_Tab**: 검토 화면의 개별 탭 (대장, 요약문, 사진대지)
- **Finalize**: 사용자가 검토를 완료하고 데이터를 확정하는 행위
- **Inline_Edit**: 표 셀을 직접 클릭하여 수정하는 방식

## Requirements

### Requirement 1: 대장 검토 및 편집

**User Story:** As a CM단 문서 담당자, I want 생성된 대장을 표 형태로 검토하고 수정할 수 있도록, so that 오류를 보고서 생성 전에 수정할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 검토 화면을 열면, THE System SHALL 문서 유형별 대장을 탭으로 구분하여 표시한다.
2. THE System SHALL 대장 데이터를 편집 가능한 테이블로 표시한다 (inline edit).
3. WHEN 사용자가 셀을 수정하면, THE System SHALL 변경 사항을 즉시 저장하고 수정 표시를 한다.
4. THE System SHALL 행 추가/삭제 기능을 제공한다.
5. THE System SHALL 수정된 셀을 시각적으로 구분(하이라이트)한다.
6. WHEN 사용자가 '원본 복원'을 요청하면, THE System SHALL 자동 추출 결과로 해당 셀을 되돌린다.

### Requirement 2: 요약문 검토 및 편집

**User Story:** As a CM단 문서 담당자, I want AI 생성 요약문을 편집할 수 있도록, so that 문맥에 맞게 내용을 조정할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 요약문 탭을 열면, THE System SHALL 섹션별 요약문을 텍스트 에디터로 표시한다.
2. THE System SHALL 마크다운 기본 서식(굵게, 목록)을 지원하는 간단한 에디터를 제공한다.
3. WHEN 사용자가 요약문을 수정하면, THE System SHALL 자동 저장(auto-save)을 5초 간격으로 수행한다.
4. THE System SHALL 'AI 재생성' 버튼을 제공하여 현재 데이터로 요약문을 다시 생성할 수 있도록 한다.
5. THE System SHALL 글자 수 카운터를 표시한다.

### Requirement 3: 사진대지 검토 및 편집

**User Story:** As a CM단 문서 담당자, I want 사진대지 배치를 검토하고 사진을 교체하거나 캡션을 수정할 수 있도록, so that 최종 사진대지의 품질을 보장할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 사진대지 탭을 열면, THE System SHALL 페이지별 사진 배치를 미리보기로 표시한다.
2. THE System SHALL 개별 사진의 캡션을 직접 편집할 수 있도록 한다.
3. THE System SHALL 사진 순서를 드래그&드롭으로 변경할 수 있도록 한다.
4. THE System SHALL 개별 사진을 다른 파일로 교체할 수 있도록 파일 선택 기능을 제공한다.
5. THE System SHALL 사진을 삭제하면 나머지 사진을 자동으로 재배치한다.

### Requirement 4: 최종 확정

**User Story:** As a CM단 문서 담당자, I want 검토를 완료하고 데이터를 확정할 수 있도록, so that 확정된 데이터로 최종 보고서가 생성된다.

#### Acceptance Criteria

1. WHEN 사용자가 '확정' 버튼을 클릭하면, THE System SHALL 모든 탭의 데이터를 최종 확정 상태로 저장한다.
2. THE System SHALL 확정 전 미입력/미검토 항목이 있으면 경고를 표시한다.
3. WHEN 데이터가 확정되면, THE System SHALL collection_job 상태를 REVIEWED로 변경한다.
4. THE System SHALL 확정 후에도 재편집이 가능하도록 한다 (확정 해제 기능).
