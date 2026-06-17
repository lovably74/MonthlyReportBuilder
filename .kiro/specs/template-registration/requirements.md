# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합·자동생성 애플리케이션의 "월간보고서 HWPX 양식 등록" 기능에 대한 요구사항을 정의한다.

월간보고서 양식 등록은 자동취합 후 생성할 월간보고서의 기반이 되는 HWPX 템플릿 파일을 시스템에 등록하고, 내부 태그를 분석하여 데이터 삽입 위치를 파악하는 기능이다. 등록된 템플릿에서 탐지된 태그는 이후 자동취합 결과(대장, 사진대지, 요약문)를 보고서에 삽입할 때 위치 기준으로 활용된다.

본 기능은 환경설정 프로필(settings_profile)에 종속되며, 하나의 프로필에 여러 버전의 템플릿을 등록할 수 있다. HWPX 파일은 한글 2022 이상에서 생성되는 ZIP 기반 문서 포맷으로, 내부에 Contents/section*.xml 파일을 포함한다.

## Glossary

- **Template_Manager**: HWPX 템플릿의 업로드, 분석, 태그 관리, 삭제를 관리하는 시스템 컴포넌트
- **Template**: 월간보고서 생성의 기반이 되는 HWPX 파일과 그에 연결된 메타데이터(detected_tags, version 등)를 포함하는 데이터 단위 (서버 DB의 report_template 테이블 레코드)
- **HWPX_File**: 한글 2022 이상에서 생성되는 ZIP 기반 문서 포맷. 내부에 Contents/section*.xml 파일을 포함하며, 확장자는 .hwpx임
- **Template_Tag**: HWPX 내부 XML에서 탐지되는 텍스트 패턴으로, 자동취합 데이터가 삽입될 위치를 나타냄 (예: PROJECT_NAME, TFA_LIST, PHOTO_PROGRESS)
- **Tag_Parser**: HWPX 파일 내부 XML을 파싱하여 Template_Tag를 자동 탐지하는 서버 컴포넌트
- **Template_Storage**: 서버에서 업로드된 HWPX 파일을 저장하는 파일 시스템 디렉토리 (%APPDATA%/CM Report Server/templates/{profile_id}/)
- **Profile**: 환경설정 프로필. Template은 반드시 하나의 Profile에 연결됨 (settings_profile 테이블의 레코드)
- **Template_Version**: 동일 프로필 내에서 동일 파일명의 템플릿을 재업로드할 때 자동으로 증가하는 정수 버전 번호
- **Tag_Mapping**: 탐지된 태그와 사용자가 수동으로 추가한 태그를 포함하는 JSON 구조의 태그 목록
- **Section_XML**: HWPX ZIP 내부의 Contents/section*.xml 파일. 문서 본문 내용을 담고 있는 XML 파일
- **Server**: 중앙 DB, 템플릿 저장소, 태그 파싱 엔진을 실행하는 서버 인스턴스
- **Client**: Tauri 기반 데스크톱 UI 애플리케이션. 서버 API를 호출하여 템플릿을 관리함

## Requirements

### Requirement 1: 템플릿 업로드

**User Story:** As a CM단 문서 담당자, I want HWPX 월간보고서 양식 파일을 시스템에 업로드할 수 있도록, so that 자동취합 결과를 삽입할 기반 문서를 등록할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 템플릿 업로드를 요청하면, THE Client SHALL 파일 선택 대화상자를 표시하되, 확장자 필터를 .hwpx로 제한하여 HWPX 파일만 선택할 수 있도록 한다.
2. WHEN 사용자가 유효한 HWPX_File을 선택하면, THE Client SHALL 해당 파일을 서버 API(POST /api/v1/templates)로 전송하고, 전송 중 진행 상태를 사용자에게 표시한다.
3. WHEN 서버가 HWPX_File을 수신하면, THE Template_Manager SHALL 해당 파일을 Template_Storage의 프로필별 디렉토리({profile_id}/)에 복사하고, report_template 테이블에 메타데이터(original_file_name, stored_path, file_type, version, detected_tags, created_at)를 저장한다.
4. WHEN 템플릿이 성공적으로 업로드되면, THE Template_Manager SHALL 업로드 완료를 나타내는 알림을 사용자에게 표시하고, 탐지된 태그 목록을 함께 표시한다.
5. IF 선택된 파일의 확장자가 .hwpx가 아니면, THEN THE Client SHALL "HWPX 파일만 업로드할 수 있습니다."라는 오류 메시지를 표시하고 업로드를 수행하지 않는다.
6. IF 업로드된 파일의 크기가 100MB를 초과하면, THEN THE Template_Manager SHALL "파일 크기가 100MB를 초과합니다."라는 오류 메시지를 반환하고 파일을 저장하지 않는다.
7. IF 서버 연결이 끊어진 상태에서 업로드를 시도하면, THEN THE Client SHALL "서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요."라는 오류 메시지를 표시하고 업로드를 수행하지 않는다.

### Requirement 2: HWPX 파일 유효성 검증

**User Story:** As a CM단 문서 담당자, I want 업로드한 HWPX 파일이 유효한 형식인지 자동으로 검증되도록, so that 손상된 파일이 등록되어 보고서 생성 시 오류가 발생하는 것을 방지할 수 있다.

#### Acceptance Criteria

1. WHEN 서버가 HWPX_File을 수신하면, THE Template_Manager SHALL 해당 파일이 유효한 ZIP 아카이브인지 검증한다.
2. WHEN 파일이 유효한 ZIP 아카이브임이 확인되면, THE Template_Manager SHALL ZIP 내부에 Contents/ 디렉토리가 존재하는지 검증한다.
3. WHEN Contents/ 디렉토리가 존재함이 확인되면, THE Template_Manager SHALL Contents/section*.xml 패턴에 매칭되는 파일이 1개 이상 존재하는지 검증한다.
4. WHEN Section_XML 파일이 존재함이 확인되면, THE Template_Manager SHALL 각 Section_XML이 well-formed XML인지 검증한다.
5. IF 파일이 유효한 ZIP 아카이브가 아니면, THEN THE Template_Manager SHALL "유효하지 않은 HWPX 파일입니다. 파일이 손상되었거나 올바른 HWPX 형식이 아닙니다."라는 오류 메시지를 반환하고 파일을 저장하지 않는다.
6. IF ZIP 내부에 Contents/ 디렉토리 또는 Section_XML 파일이 존재하지 않으면, THEN THE Template_Manager SHALL "HWPX 파일 내부 구조가 올바르지 않습니다. Contents/section*.xml 파일을 찾을 수 없습니다."라는 오류 메시지를 반환하고 파일을 저장하지 않는다.
7. IF Section_XML 중 하나라도 well-formed XML이 아니면, THEN THE Template_Manager SHALL "HWPX 내부 XML 파싱에 실패했습니다. 파일이 손상되었을 수 있습니다."라는 오류 메시지를 반환하고 파일을 저장하지 않는다.

### Requirement 3: 태그 자동 탐지

**User Story:** As a CM단 문서 담당자, I want 업로드한 HWPX 파일에서 데이터 삽입 태그가 자동으로 탐지되도록, so that 보고서 생성 시 어떤 데이터가 어디에 삽입될지 사전에 파악할 수 있다.

#### Acceptance Criteria

1. WHEN HWPX_File의 유효성 검증이 완료되면, THE Tag_Parser SHALL 모든 Section_XML의 텍스트 노드를 순회하며 사전 정의된 Template_Tag 패턴을 검색한다.
2. THE Tag_Parser SHALL 다음 텍스트 태그를 탐지 대상으로 인식한다: PROJECT_NAME, WRITE_YYMM, SUMMARY_TEXT, REPORT_ROUND, REPORT_PERIOD, TFA_LIST, IRR_LIST, TR_LIST, DN_LIST, NCR_LIST, FI_LIST, SCAR_LIST, TFA_IMG, IRR_IMG, DN_IMG, NCR_IMG, FI_IMG, SCAR_IMG, PHOTO_SITE_VIEW, PHOTO_PROGRESS.
3. WHEN 태그가 탐지되면, THE Tag_Parser SHALL 각 태그에 대해 태그명, 해당 태그가 발견된 Section_XML 파일명, 해당 Section 내 위치 정보를 기록한다.
4. WHEN 태그 탐지가 완료되면, THE Template_Manager SHALL 탐지 결과를 JSON 형식으로 report_template 테이블의 detected_tags 컬럼에 저장한다.
5. IF Section_XML 내에 동일한 태그가 여러 번 존재하면, THEN THE Tag_Parser SHALL 각 발생 위치를 모두 기록하여 detected_tags에 포함한다.
6. IF 탐지된 태그가 하나도 없으면, THEN THE Template_Manager SHALL "템플릿에서 인식 가능한 태그를 찾을 수 없습니다. 태그를 수동으로 추가하거나 템플릿 파일을 확인해 주세요."라는 경고 메시지를 반환하고, detected_tags를 빈 배열([])로 저장한다.

### Requirement 4: 태그 매핑 관리

**User Story:** As a CM단 문서 담당자, I want 탐지된 태그를 확인하고 수동으로 태그를 추가하거나 제거할 수 있도록, so that 자동 탐지에서 누락된 태그를 보완하거나 불필요한 태그를 제외할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 템플릿 상세 화면에서 태그 목록을 조회하면, THE Client SHALL 자동 탐지된 태그와 사용자가 수동 추가한 태그를 구분하여 표시한다.
2. WHEN 사용자가 새로운 태그를 수동으로 추가하면, THE Template_Manager SHALL 해당 태그를 Tag_Mapping에 추가하고 detected_tags JSON을 갱신한다.
3. WHEN 사용자가 기존 태그를 삭제하면, THE Template_Manager SHALL 해당 태그를 Tag_Mapping에서 제거하고 detected_tags JSON을 갱신한다.
4. WHEN 태그 매핑이 변경되면, THE Template_Manager SHALL PUT /api/v1/templates/{id}/tags 엔드포인트를 통해 서버에 변경 사항을 저장한다.
5. IF 사용자가 이미 존재하는 태그명과 동일한 태그를 추가하려고 하면, THEN THE Template_Manager SHALL "동일한 이름의 태그가 이미 존재합니다."라는 오류 메시지를 표시하고 태그를 추가하지 않는다.
6. IF 사용자가 빈 문자열 또는 공백만으로 구성된 태그명을 입력하면, THEN THE Template_Manager SHALL "태그명은 필수 입력값입니다."라는 오류 메시지를 표시하고 태그를 추가하지 않는다.
7. WHEN 태그 매핑이 성공적으로 저장되면, THE Template_Manager SHALL 저장 완료를 나타내는 알림을 사용자에게 표시한다.

### Requirement 5: 템플릿 버전 관리

**User Story:** As a CM단 문서 담당자, I want 동일한 프로필에 새 버전의 양식 파일을 재업로드할 수 있도록, so that 양식이 변경되었을 때 이전 버전을 유지하면서 최신 양식을 적용할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 동일 프로필에 동일한 original_file_name을 가진 HWPX_File을 재업로드하면, THE Template_Manager SHALL 기존 Template을 유지하면서 version 값을 1 증가시킨 새로운 Template 레코드를 생성한다.
2. WHEN 새 버전이 생성되면, THE Template_Manager SHALL 새 버전의 HWPX_File을 Template_Storage에 별도의 파일명(원본명_v{version}.hwpx)으로 저장한다.
3. WHEN 새 버전이 생성되면, THE Template_Manager SHALL 새 버전에 대해 태그 자동 탐지를 독립적으로 수행하여 detected_tags를 저장한다.
4. THE Template_Manager SHALL 동일 프로필 내에서 동일 파일명에 대한 모든 버전의 이력을 유지하여, 사용자가 이전 버전의 태그 정보를 조회할 수 있도록 한다.
5. WHEN 사용자가 템플릿 목록을 조회하면, THE Template_Manager SHALL 각 템플릿의 최신 버전을 기본으로 표시하되, 버전 이력 접근 수단을 제공한다.

### Requirement 6: 템플릿 목록 조회

**User Story:** As a CM단 문서 담당자, I want 현재 프로필에 등록된 모든 템플릿 목록을 확인할 수 있도록, so that 등록된 양식 현황을 파악하고 관리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 템플릿 관리 화면에 접근하면, THE Client SHALL GET /api/v1/templates 엔드포인트를 호출하여 현재 프로필에 연결된 모든 Template 목록을 조회한다.
2. THE Client SHALL 템플릿 목록에 각 Template의 original_file_name, version, created_at, 탐지된 태그 수를 표시한다.
3. THE Client SHALL 템플릿 목록을 created_at 내림차순(최신순)으로 정렬하여 표시한다.
4. WHEN 사용자가 목록에서 특정 Template을 선택하면, THE Client SHALL GET /api/v1/templates/{id} 엔드포인트를 호출하여 해당 템플릿의 상세 정보와 탐지된 태그 목록을 표시한다.
5. IF 현재 프로필에 등록된 Template이 없으면, THEN THE Client SHALL "등록된 템플릿이 없습니다. HWPX 양식 파일을 업로드해 주세요."라는 안내 메시지를 표시하고 업로드 버튼을 제공한다.
6. IF 템플릿 목록 로드에 실패하면, THEN THE Client SHALL 로드 실패 원인을 포함한 오류 메시지를 표시하고 재시도 수단을 제공한다.

### Requirement 7: 템플릿 구조 미리보기

**User Story:** As a CM단 문서 담당자, I want 업로드한 템플릿의 내부 구조를 미리볼 수 있도록, so that 태그 위치와 문서 구성을 시각적으로 확인할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 템플릿 상세 화면에서 구조 미리보기를 요청하면, THE Client SHALL 해당 HWPX_File 내부의 Section_XML 목록과 각 섹션에서 탐지된 태그 위치를 트리 구조로 표시한다.
2. THE Client SHALL 미리보기에서 각 Section_XML의 파일명을 노드로 표시하고, 하위에 해당 섹션에서 발견된 Template_Tag를 나열한다.
3. THE Client SHALL 탐지된 태그를 시각적으로 강조 표시하여 일반 텍스트와 구분한다.
4. IF 템플릿에 탐지된 태그가 없으면, THEN THE Client SHALL 섹션 목록만 표시하고 "탐지된 태그 없음"이라는 안내 문구를 표시한다.

### Requirement 8: 템플릿 삭제

**User Story:** As a CM단 문서 담당자, I want 불필요한 템플릿을 삭제할 수 있도록, so that 사용하지 않는 양식을 정리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 템플릿 삭제를 요청하면, THE Client SHALL "템플릿 '[파일명]'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."라는 확인 대화상자를 표시한다.
2. WHEN 사용자가 삭제 확인을 승인하면, THE Template_Manager SHALL DELETE /api/v1/templates/{id} 엔드포인트를 통해 해당 Template의 DB 레코드와 Template_Storage의 물리적 파일을 모두 삭제한다.
3. IF 사용자가 삭제 확인 대화상자에서 취소를 선택하면, THEN THE Client SHALL 삭제를 수행하지 않고 현재 화면을 유지한다.
4. WHEN 템플릿 삭제가 완료되면, THE Client SHALL 삭제 완료 메시지를 표시하고 템플릿 목록에서 해당 항목을 즉시 제거한다.
5. IF 삭제 중 서버 오류가 발생하면, THEN THE Client SHALL 삭제 실패 원인을 포함한 오류 메시지를 표시하고 재시도 수단을 제공한다.

### Requirement 9: 프로필 연계 및 데이터 무결성

**User Story:** As a CM단 문서 담당자, I want 템플릿이 특정 프로필에 종속되어 관리되도록, so that 프로필별로 독립적인 양식 관리가 가능하다.

#### Acceptance Criteria

1. THE Template_Manager SHALL 모든 Template을 정확히 하나의 Profile에 연결하여 저장한다 (report_template.profile_id 외래키 참조).
2. WHEN 사용자가 프로필을 전환하면, THE Client SHALL 해당 프로필에 연결된 Template 목록만 조회하여 표시한다.
3. IF 연결된 Profile이 삭제되면, THEN THE Template_Manager SHALL 해당 Profile에 연결된 모든 Template의 DB 레코드와 Template_Storage의 물리적 파일을 함께 삭제한다 (CASCADE 삭제).
4. THE Template_Manager SHALL report_template 테이블의 profile_id 컬럼에 외래키 제약 조건을 설정하여, 존재하지 않는 Profile을 참조하는 Template의 생성을 방지한다.

### Requirement 10: 태그 탐지 결과 직렬화 라운드트립

**User Story:** As a 시스템, I want 태그 탐지 결과를 JSON으로 저장하고 다시 읽었을 때 동일한 구조가 복원되도록, so that 태그 데이터의 무결성이 보장된다.

#### Acceptance Criteria

1. THE Template_Manager SHALL detected_tags 필드를 JSON 문자열로 직렬화하여 SQLite TEXT 컬럼에 저장한다.
2. WHEN detected_tags를 읽을 때, THE Template_Manager SHALL JSON 문자열을 파싱하여 태그명, 섹션 파일명, 위치 정보를 포함한 태그 객체 배열로 복원한다.
3. FOR ALL 유효한 detected_tags JSON을 저장 후 조회했을 때, THE Template_Manager SHALL 원본과 동일한 태그 목록을 반환한다 (라운드트립 보장).
4. IF detected_tags 컬럼의 JSON 파싱에 실패하면, THEN THE Template_Manager SHALL 파싱 실패를 로그에 기록하고, 빈 태그 목록([])을 반환하여 서비스 가용성을 유지한다.

