# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "AI 요약" 기능에 대한 요구사항을 정의한다.

AI 요약은 로컬 LLM(Ollama/LM Studio)을 활용하여 추출된 데이터를 기반으로 보고서 요약문을 자동 생성하는 기능이다. 인터넷 연결 없이 동일 LAN 내 서버의 LLM 엔진을 사용한다.

**연동 관계:**
- **의존**: Spec 09 (data-extraction) — 추출된 텍스트 데이터
- **의존**: LLM 서버 설정 (Ollama/LM Studio API 엔드포인트)
- **제공**: Spec 11 (hwpx-renderer)에 요약문 텍스트 전달
- DB: ai_summary 테이블

## Glossary

- **LLM_Engine**: 로컬 실행 대규모 언어 모델 (Ollama 또는 LM Studio)
- **Summary_Prompt**: LLM에 전달하는 요약 생성 프롬프트
- **Summary_Result**: LLM이 생성한 요약문 결과
- **OpenAI_Compatible_API**: Ollama/LM Studio가 제공하는 OpenAI 호환 REST API

## Requirements

### Requirement 1: LLM 연동 설정

**User Story:** As a 시스템 관리자, I want 로컬 LLM 서버 연결을 설정할 수 있도록, so that AI 요약 기능을 사용할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 LLM 설정을 구성하면, THE System SHALL API 엔드포인트 URL, 모델명, 최대 토큰 수를 저장한다.
2. WHEN 사용자가 'LLM 연결 테스트'를 요청하면, THE System SHALL 지정된 엔드포인트에 ping 요청을 보내고 연결 상태를 표시한다.
3. THE System SHALL OpenAI 호환 API 형식(/v1/chat/completions)을 사용한다.
4. IF LLM 서버에 연결할 수 없으면, THEN THE System SHALL 연결 실패 메시지를 표시하고 AI 요약 기능을 비활성화한다.
5. THE System SHALL LLM 요청 타임아웃을 60초로 설정하되, 사용자가 조정할 수 있도록 한다.

### Requirement 2: 요약문 생성

**User Story:** As a CM단 문서 담당자, I want 추출된 데이터를 기반으로 보고서 요약문이 자동 생성되도록, so that 요약문 작성 시간을 줄일 수 있다.

#### Acceptance Criteria

1. WHEN 요약 생성이 요청되면, THE System SHALL 추출된 데이터를 프롬프트에 포함하여 LLM에 전달한다.
2. THE System SHALL 프롬프트에 문서 유형, 보고 기간, 프로젝트명 등 컨텍스트 정보를 포함한다.
3. WHEN LLM 응답을 수신하면, THE System SHALL 응답을 ai_summary 테이블에 저장한다.
4. THE System SHALL 요약문을 '공정 요약', '안전 요약', '품질 요약', '종합 의견' 등 섹션별로 생성할 수 있도록 지원한다.
5. IF LLM 응답이 비어있거나 오류인 경우, THEN THE System SHALL 재시도 옵션과 수동 입력 옵션을 제공한다.
6. THE System SHALL 요약문 생성 요청 시 진행 표시(로딩 스피너)를 표시한다.

### Requirement 3: 요약문 관리

**User Story:** As a CM단 문서 담당자, I want 생성된 요약문을 검토하고 수정할 수 있도록, so that AI가 놓친 내용을 보완할 수 있다.

#### Acceptance Criteria

1. WHEN 요약문이 생성되면, THE System SHALL 사용자에게 검토·편집 화면을 제공한다.
2. THE System SHALL 사용자가 요약문을 직접 수정할 수 있는 텍스트 에디터를 제공한다.
3. WHEN 사용자가 요약문을 수정하면, THE System SHALL 수정된 내용을 DB에 저장하고 is_edited=true로 표시한다.
4. THE System SHALL '재생성' 버튼을 제공하여 프롬프트를 변경하고 다시 생성할 수 있도록 한다.
5. THE System SHALL 이전 생성 이력(버전)을 최대 5개까지 보관한다.
