# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "자동 분류" 기능에 대한 요구사항을 정의한다.

자동 분류는 복사된 파일을 15개 문서 유형 중 하나로 분류하는 기능으로, 폴더명/파일명 키워드 매칭, 본문 텍스트 키워드 매칭, 유사도 비교를 단계적으로 수행하여 분류 결과와 신뢰도를 산출한다.

**연동 관계:**
- **의존**: Spec 03 (document-sample) — 분류 기준 (키워드, 유사도 임계값, 확장자)
- **의존**: Spec 07 (file-copy) — 복사된 파일 목록 (collected_file)
- **의존**: Spec 13 (ai-summary) — LLM 보조 분류 옵션 (선택적)
- **제공**: Spec 09 (data-extraction)에 분류된 파일 목록 전달

## Glossary

- **Classification_Result**: 파일별 분류 결과 (유형, 신뢰도, 분류방법)
- **Confidence_Score**: 분류 신뢰도 (0.0~1.0)
- **Classification_Method**: 분류에 사용된 방법 (folder_keyword, filename_keyword, content_keyword, similarity, llm_assist, manual)
- **UNKNOWN**: 분류 불가 파일에 부여하는 기본 유형

## Requirements

### Requirement 1: 키워드 기반 분류

**User Story:** As a CM단 문서 담당자, I want 파일이 키워드 기반으로 자동 분류되도록, so that 수백 개의 파일을 수동으로 분류하는 수고를 줄일 수 있다.

#### Acceptance Criteria

1. WHEN 분류가 시작되면, THE System SHALL 다음 순서로 키워드 매칭을 수행한다: ① 폴더명, ② 파일명, ③ 본문 텍스트.
2. WHEN 폴더명 또는 파일명에서 include_keywords 매칭이 발생하면, THE System SHALL 해당 문서 유형으로 분류하고 confidence=0.9 이상을 부여한다.
3. WHEN 본문 텍스트에서 키워드 매칭이 발생하면, THE System SHALL 매칭된 키워드 수/전체 키워드 수 비율로 confidence를 산출한다.
4. IF exclude_keywords에 매칭되면, THEN THE System SHALL 해당 유형에서 제외한다.
5. IF 여러 유형에 매칭되면, THEN THE System SHALL confidence가 가장 높은 유형을 선택한다.
6. WHEN 분류가 완료되면, THE System SHALL collected_file 레코드에 classified_type, confidence, classification_method를 기록한다.

### Requirement 2: 유사도 기반 분류

**User Story:** As a CM단 문서 담당자, I want 키워드 매칭 실패 시 샘플 유사도로 분류되도록, so that 키워드가 포함되지 않은 문서도 분류할 수 있다.

#### Acceptance Criteria

1. IF 키워드 매칭으로 분류되지 않은 파일에 대해, THE System SHALL 등록된 샘플 파일과의 텍스트 유사도를 계산한다.
2. WHEN 유사도가 해당 문서 유형의 similarity_threshold 이상이면, THE System SHALL 해당 유형으로 분류하고 유사도 값을 confidence로 설정한다.
3. THE System SHALL 유사도 계산 시 TF-IDF 또는 코사인 유사도를 사용한다.
4. IF 모든 유형과의 유사도가 threshold 미만이면, THEN THE System SHALL 해당 파일을 UNKNOWN으로 분류한다.

### Requirement 3: 분류 결과 관리

**User Story:** As a CM단 문서 담당자, I want 분류 결과를 확인하고 수정할 수 있도록, so that 오분류된 파일을 바로잡을 수 있다.

#### Acceptance Criteria

1. WHEN 분류가 완료되면, THE System SHALL 유형별 파일 수, UNKNOWN 파일 수, 평균 신뢰도를 요약 표시한다.
2. THE System SHALL 사용자가 분류 결과를 수동으로 변경(재분류)할 수 있도록 한다.
3. WHEN 사용자가 수동 재분류하면, THE System SHALL classification_method를 'manual'로 변경하고 confidence를 1.0으로 설정한다.
4. THE System SHALL confidence < 0.5인 파일을 '확인 필요' 표시로 강조한다.
5. WHEN 분류 작업이 완료되면, THE System SHALL collection_job 상태를 CLASSIFIED로 변경한다.
