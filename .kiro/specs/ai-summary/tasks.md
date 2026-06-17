# Implementation Plan: AI 요약 (ai-summary)

## Overview

로컬 LLM(Ollama/LM Studio)과 연동하여 추출된 데이터 기반의 보고서 요약문을 자동 생성하는 기능을 구현한다. OpenAI 호환 API를 통해 통신하며, ai_summary 테이블에 결과를 저장한다.

## Tasks

- [ ] 1. 데이터 모델 및 LLM 클라이언트
  - [ ] 1.1 ai_summary 테이블 생성
    - `app/models/ai_summary.py`에 ORM 모델 정의
    - FK: job_id → collection_job.id (CASCADE)
  - [ ] 1.2 LLMClient 구현
    - `app/services/llm_client.py`
    - OpenAI 호환 /v1/chat/completions 호출
    - 타임아웃, 재시도, 연결 테스트(ping)
  - [ ] 1.3 프롬프트 템플릿 정의
    - `app/services/prompt_templates.py`
    - 섹션별(공정, 안전, 품질, 종합) 프롬프트

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 AISummaryService 구현
    - generate_summary, regenerate_section, update_summary, test_connection
    - 버전 관리 (최대 5개 이력)
  - [ ] 2.2 AI Summary API Router
    - POST /api/v1/llm/test
    - POST /api/v1/jobs/{job_id}/summary
    - GET /api/v1/jobs/{job_id}/summary
    - PUT /api/v1/jobs/{job_id}/summary/{section}
    - POST /api/v1/jobs/{job_id}/summary/{section}/regenerate

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 LLM 설정 UI (엔드포인트, 모델, 타임아웃)
  - [ ] 3.2 요약 생성 진행 + 결과 에디터
  - [ ] 3.3 API Client 및 Store

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 섹션 중복 방지, 버전 연속성, 편집 보존
  - [ ] 4.2 Unit Tests: 프롬프트 생성, LLMClient 모킹
  - [ ] 4.3 Integration Tests: 모킹 기반 전체 플로우

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] }
  ]
}
```

## Notes

- LLM 서버 기본 엔드포인트: http://localhost:11434/v1 (Ollama), http://localhost:1234/v1 (LM Studio)
- LLM 연결 불가 시 AI 요약 기능 비활성화 (수동 입력으로 대체)
- 인터넷 연결 불필요 (동일 LAN 내 통신만)
