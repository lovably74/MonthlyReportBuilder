# Design Document: 자동 분류 (document-classification)

## Overview

자동 분류는 collected_file을 15개 문서 유형 중 하나로 분류하는 엔진이다. 폴더명/파일명/본문 키워드 매칭과 샘플 유사도 비교를 단계적으로 수행하며, 선택적으로 LLM 보조 분류를 활용할 수 있다.

### 핵심 설계 결정

1. **단계적 분류**: 폴더명 → 파일명 → 본문 키워드 → 유사도 → (LLM) 순서로 시도.
2. **조기 종료**: 높은 confidence 결과가 나오면 이후 단계를 건너뜀.
3. **UNKNOWN 폴백**: 모든 분류 시도 실패 시 UNKNOWN으로 분류.
4. **수동 재분류 우선**: 사용자 수동 분류는 confidence=1.0으로 최우선.

## Architecture

### 분류 파이프라인

```
collected_file 목록
  → FolderKeywordMatcher (경로 기반)
    → confidence >= 0.9 → 확정
  → FilenameKeywordMatcher (파일명 기반)
    → confidence >= 0.9 → 확정
  → ContentKeywordMatcher (본문 텍스트 기반)
    → confidence >= threshold → 확정
  → SimilarityMatcher (샘플 대비 유사도)
    → confidence >= threshold → 확정
  → UNKNOWN (모두 실패)
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/classification_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/classify` | POST | 분류 시작 |
| `/api/v1/jobs/{job_id}/classification` | GET | 분류 결과 조회 |
| `/api/v1/jobs/{job_id}/files/{file_id}/classify` | PUT | 수동 재분류 |

#### Service Layer

```python
class ClassificationService:
    async def classify_job(self, job_id: int) -> ClassificationResult
    async def reclassify_file(self, file_id: int, type_code: str) -> CollectedFile

class ClassificationPipeline:
    def classify(self, file: CollectedFile, configs: list[DocumentTypeConfig]) -> ClassificationResult
    
class FolderKeywordMatcher:
    def match(self, file_path: str, keywords: list[str]) -> float

class SimilarityMatcher:
    def compute_similarity(self, text: str, sample_texts: list[str]) -> float
```

### Frontend Components

| 컴포넌트 | 설명 |
|----------|------|
| `ClassificationPanel` | 분류 실행 + 결과 요약 |
| `ClassificationResultTable` | 파일별 분류 결과 테이블 |
| `ReclassifyDialog` | 수동 재분류 대화상자 |
| `ConfidenceBadge` | 신뢰도 배지 (색상 코드) |

## Data Models

collected_file 테이블의 classified_type, confidence, classification_method 컬럼을 사용한다. (Spec 07 참조)

### Pydantic Schemas

```python
class ClassificationResult(BaseModel):
    job_id: int
    total_files: int
    classified_count: int
    unknown_count: int
    avg_confidence: float
    by_type: dict[str, int]  # type_code -> count

class FileClassification(BaseModel):
    file_id: int
    classified_type: str
    confidence: float
    classification_method: str
```

## Correctness Properties

### Property 1: 분류 완전성
*For any* job의 모든 collected_file에 대해, 분류 완료 후 classified_type이 None인 파일은 없어야 한다.

### Property 2: exclude_keywords 우선
*For any* exclude_keywords에 매칭되는 파일은 해당 유형으로 분류되지 않아야 한다.

### Property 3: 수동 재분류 최우선
*For any* 수동 재분류된 파일은 classification_method='manual', confidence=1.0이어야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| JOB_NOT_FOUND | 404 | 존재하지 않는 job |
| NO_FILES_TO_CLASSIFY | 400 | 복사된 파일 없음 |
| INVALID_TYPE_CODE | 422 | 잘못된 문서 유형 코드 |
| TEXT_EXTRACTION_FAILED | 500 | 본문 텍스트 추출 실패 |

## Testing Strategy

- **Property Tests**: 분류 완전성, exclude_keywords 우선, 수동 재분류
- **Unit Tests**: 키워드 매처 개별 동작, 유사도 계산
- **Integration Tests**: 전체 파이프라인 플로우, 다중 유형 경합
- **Frontend Tests**: ClassificationResultTable 렌더링, ReclassifyDialog
