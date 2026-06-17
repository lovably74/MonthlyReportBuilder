# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "취합 문서 샘플 등록" 기능에 대한 요구사항을 정의한다.

취합 문서 샘플 등록은 15개 문서 유형(공문, 회의록, 공정현황, 안전점검, 검측기록, 자재반입, 기성내역, 시험성과, 품질시험, 사진대지, 인력현황, 장비현황, 환경관리, NCR, 기타)에 대한 샘플 파일과 분류 기준(키워드, 유사도 임계값, 확장자)을 등록하는 기능이다.

**연동 관계:**
- **의존**: Spec 01 (settings-profile) — `document_type_config.profile_id` FK로 프로필에 종속
- **의존**: Spec 02 (template-registration) — 환경설정 화면에서 함께 구성
- **제공**: Spec 08 (document-classification)에 분류 기준(키워드, 유사도, 확장자) 제공

## Glossary

- **Document_Type**: 15개 문서 유형 중 하나 (공문, 회의록, 공정현황 등)
- **Document_Type_Config**: 문서 유형별 분류 기준 설정 레코드
- **Document_Sample**: 특정 문서 유형의 실제 샘플 파일
- **Include_Keywords**: 해당 문서 유형으로 분류할 때 사용하는 포함 키워드 목록
- **Exclude_Keywords**: 해당 문서 유형에서 제외할 키워드 목록
- **Similarity_Threshold**: 키워드 매칭 시 유사도 기준값 (0.0~1.0)
- **Supported_Extensions**: 해당 문서 유형에서 지원하는 파일 확장자 목록

## Requirements

### Requirement 1: 문서 유형 설정 조회 및 초기화

**User Story:** As a CM단 문서 담당자, I want 15개 문서 유형의 분류 설정을 한눈에 확인할 수 있도록, so that 자동 분류 기준을 효율적으로 관리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 프로필의 문서 샘플 탭을 열면, THE System SHALL 15개 문서 유형 목록을 표시하며, 각 유형별로 등록된 샘플 수, 키워드 수, 활성화 상태를 표시한다.
2. WHEN 프로필에 문서 유형 설정이 없는 상태에서 탭을 열면, THE System SHALL 15개 기본 문서 유형을 자동으로 생성하고 기본 키워드와 확장자를 설정한다.
3. WHEN 문서 유형 목록이 표시되면, THE System SHALL 각 유형의 display_name, include_keywords 수, sample 수, is_active 상태를 표시한다.
4. IF 서버 연결이 끊어진 상태에서 탭을 열면, THEN THE System SHALL 로컬 캐시된 설정을 읽기 전용으로 표시한다.

### Requirement 2: 문서 유형별 키워드 설정

**User Story:** As a CM단 문서 담당자, I want 각 문서 유형별로 포함/제외 키워드를 설정할 수 있도록, so that 자동 분류의 정확도를 높일 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 특정 문서 유형의 include_keywords를 설정하면, THE System SHALL 쉼표로 구분된 키워드 목록을 저장하고 각 키워드를 앞뒤 공백 제거 후 저장한다.
2. WHEN 사용자가 특정 문서 유형의 exclude_keywords를 설정하면, THE System SHALL 쉼표로 구분된 제외 키워드 목록을 저장한다.
3. IF 사용자가 빈 키워드(공백만)를 입력하면, THEN THE System SHALL 해당 키워드를 무시하고 저장하지 않는다.
4. WHEN 키워드가 수정되면, THE System SHALL updated_at을 갱신하고 변경 사항을 서버 DB에 즉시 반영한다.
5. THE System SHALL 각 문서 유형별 키워드 수를 최대 50개로 제한한다.

### Requirement 3: 샘플 파일 등록

**User Story:** As a CM단 문서 담당자, I want 각 문서 유형별로 실제 샘플 파일을 등록할 수 있도록, so that 유사도 기반 분류의 기준 데이터를 제공할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 특정 문서 유형에 샘플 파일 등록을 요청하면, THE System SHALL 파일 선택 대화상자를 표시하고 선택된 파일을 서버에 업로드한다.
2. WHEN 샘플 파일이 업로드되면, THE System SHALL 파일을 `{DATA_DIR}/samples/{profile_id}/{type_code}/` 경로에 저장하고 DB에 메타데이터를 기록한다.
3. THE System SHALL 문서 유형별 샘플 파일 수를 최대 5개로 제한한다.
4. IF 샘플 파일 크기가 50MB를 초과하면, THEN THE System SHALL 업로드를 거부하고 파일 크기 초과 오류를 표시한다.
5. WHEN 사용자가 샘플 파일 삭제를 요청하면, THE System SHALL DB 레코드와 물리 파일을 함께 삭제한다.
6. THE System SHALL 샘플 파일의 원본 파일명, 크기, 업로드 일자를 목록에 표시한다.

### Requirement 4: 문서 유형별 상세 설정

**User Story:** As a CM단 문서 담당자, I want 각 문서 유형의 유사도 임계값, 지원 확장자, 대장 생성 여부를 설정할 수 있도록, so that 세밀한 분류 및 처리 기준을 제어할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 similarity_threshold를 설정하면, THE System SHALL 0.0~1.0 범위의 소수점 값을 저장한다. 기본값은 0.7이다.
2. WHEN 사용자가 supported_extensions를 설정하면, THE System SHALL 쉼표로 구분된 확장자 목록(예: hwpx,docx,xlsx,pdf)을 저장한다.
3. WHEN 사용자가 generate_ledger 옵션을 설정하면, THE System SHALL 해당 문서 유형의 대장 자동 생성 여부(true/false)를 저장한다.
4. WHEN 사용자가 include_in_appendix 옵션을 설정하면, THE System SHALL 해당 문서 유형의 Appendix 삽입 여부를 저장한다.
5. IF similarity_threshold가 0.0~1.0 범위를 벗어나면, THEN THE System SHALL 유효하지 않은 값임을 나타내는 오류를 표시한다.

### Requirement 5: 문서 유형 활성화/비활성화

**User Story:** As a CM단 문서 담당자, I want 특정 문서 유형을 비활성화할 수 있도록, so that 해당 현장에서 불필요한 유형을 분류 대상에서 제외할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 문서 유형을 비활성화(is_active=false)하면, THE System SHALL 해당 유형을 자동 분류 대상에서 제외한다.
2. WHEN 사용자가 비활성화된 문서 유형을 다시 활성화하면, THE System SHALL 해당 유형을 자동 분류 대상에 포함한다.
3. THE System SHALL 비활성화된 유형도 목록에 표시하되 비활성 상태임을 시각적으로 구분한다.
