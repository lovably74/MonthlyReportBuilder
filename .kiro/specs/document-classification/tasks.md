# Implementation Plan: 자동 분류 (document-classification)

## Overview

collected_file을 15개 문서 유형으로 분류하는 엔진을 구현한다. 폴더명/파일명/본문 키워드 매칭과 샘플 유사도 비교를 단계적으로 수행하며, 수동 재분류를 지원한다.

## Tasks

- [ ] 1. 분류 엔진 구현
  - [ ] 1.1 ClassificationPipeline 구현
    - `app/services/classification_pipeline.py`에 단계적 분류 로직
    - 조기 종료: confidence >= 0.9 시 이후 단계 생략
  - [ ] 1.2 FolderKeywordMatcher 구현
    - 파일 경로에서 폴더명 추출 → include_keywords 매칭
  - [ ] 1.3 FilenameKeywordMatcher 구현
    - 파일명에서 키워드 매칭
  - [ ] 1.4 ContentKeywordMatcher 구현
    - 본문 텍스트 추출 → 키워드 매칭 → 비율로 confidence 산출
  - [ ] 1.5 SimilarityMatcher 구현
    - TF-IDF + 코사인 유사도 계산 (scikit-learn 또는 직접 구현)

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 ClassificationService 구현
    - classify_job: 전체 파일 분류, reclassify_file: 수동 재분류
  - [ ] 2.2 Classification API Router
    - POST /api/v1/jobs/{job_id}/classify
    - GET /api/v1/jobs/{job_id}/classification
    - PUT /api/v1/jobs/{job_id}/files/{file_id}/classify

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 ClassificationPanel + ClassificationResultTable
  - [ ] 3.2 ReclassifyDialog + ConfidenceBadge
  - [ ] 3.3 API Client 및 Store

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 분류 완전성, exclude 우선, 수동 재분류
  - [ ] 4.2 Unit Tests: 각 Matcher 개별 동작
  - [ ] 4.3 Integration Tests: 전체 파이프라인, 다중 유형 경합

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] }
  ]
}
```

## Notes

- 분류 결과는 collected_file.classified_type, confidence, classification_method에 저장
- UNKNOWN 분류는 모든 시도 실패 시 부여 (confidence=0.0)
- 본문 텍스트 추출은 Spec 09의 파서를 간소화한 버전 사용
