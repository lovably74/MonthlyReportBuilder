# Design Document: AI 요약 (ai-summary)

## Overview

AI 요약은 로컬 LLM(Ollama/LM Studio)을 활용하여 추출된 데이터를 기반으로 보고서 섹션별 요약문을 생성하는 기능이다. OpenAI 호환 API를 통해 LLM과 통신하며, 인터넷 연결 없이 동일 LAN 내에서 동작한다.

### 핵심 설계 결정

1. **OpenAI 호환 API**: /v1/chat/completions 엔드포인트 사용.
2. **프롬프트 템플릿**: 섹션별 프롬프트 템플릿을 미리 정의.
3. **버전 관리**: 생성 이력을 최대 5개까지 보관.
4. **타임아웃**: 60초 기본, 사용자 조정 가능.
5. **비활성화 가능**: LLM 연결 불가 시 수동 입력으로 대체.

## Architecture

### 통신 구조

```
Server App
  → LLMClient (/v1/chat/completions)
    → Ollama (localhost:11434) 또는 LM Studio (localhost:1234)
  → ai_summary 테이블 저장
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/ai_summary_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/llm/test` | POST | LLM 연결 테스트 |
| `/api/v1/jobs/{job_id}/summary` | POST | 요약 생성 요청 |
| `/api/v1/jobs/{job_id}/summary` | GET | 요약 결과 조회 |
| `/api/v1/jobs/{job_id}/summary/{section}` | PUT | 요약 수정 |
| `/api/v1/jobs/{job_id}/summary/{section}/regenerate` | POST | 재생성 |

#### Service Layer

```python
class AISummaryService:
    async def generate_summary(self, job_id: int, sections: list[str] = None) -> list[AISummary]
    async def regenerate_section(self, job_id: int, section: str, custom_prompt: str = None) -> AISummary
    async def update_summary(self, summary_id: int, content: str) -> AISummary
    async def test_connection(self) -> bool

class LLMClient:
    async def chat_completion(self, messages: list[dict], model: str = None) -> str
    async def ping(self) -> bool
```

## Data Models

### SQLAlchemy ORM

```python
class AISummary(Base):
    __tablename__ = "ai_summary"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("collection_job.id", ondelete="CASCADE"), nullable=False)
    section = Column(Text, nullable=False)  # progress, safety, quality, overall
    content = Column(Text, default="")
    prompt_used = Column(Text, default="")
    model_name = Column(Text, default="")
    version = Column(Integer, default=1)
    is_edited = Column(Boolean, default=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
```

### TypeScript 인터페이스

```typescript
interface AISummary {
  id: number;
  job_id: number;
  section: string;
  content: string;
  model_name: string;
  version: number;
  is_edited: boolean;
  created_at: string;
}

interface LLMConfig {
  endpoint_url: string;
  model_name: string;
  max_tokens: number;
  timeout_seconds: number;
}
```

## Correctness Properties

### Property 1: 섹션 중복 방지
*For any* job_id + section 조합에 대해, 동일 버전의 ai_summary는 1개만 존재해야 한다.

### Property 2: 버전 연속성
*For any* 요약문 재생성 시, version은 이전 최대 버전 +1이어야 한다.

### Property 3: 편집 상태 보존
*For any* is_edited=true인 요약문은 자동 재생성으로 덮어쓰지 않아야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| LLM_CONNECTION_FAILED | 503 | LLM 서버 연결 실패 |
| LLM_TIMEOUT | 504 | LLM 응답 타임아웃 |
| LLM_EMPTY_RESPONSE | 500 | LLM 빈 응답 |
| SUMMARY_NOT_FOUND | 404 | 요약 레코드 없음 |
| NO_DATA_FOR_SUMMARY | 400 | 요약할 데이터 없음 |

## Testing Strategy

- **Property Tests**: 섹션 중복 방지, 버전 연속성, 편집 상태 보존
- **Unit Tests**: 프롬프트 생성, 응답 파싱, 타임아웃 처리
- **Integration Tests**: LLM 모킹 기반 전체 플로우
- **Frontend Tests**: 요약 에디터, 재생성 버튼, 연결 테스트 UI
