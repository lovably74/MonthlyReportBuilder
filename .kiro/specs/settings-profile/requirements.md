# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합·자동생성 애플리케이션의 "환경설정 프로필 관리" 기능에 대한 요구사항을 정의한다.

환경설정 프로필은 자동취합과 보고서 생성을 위한 기준정보를 등록하는 영역으로, 현장별·양식별·발주처별로 여러 프로필을 저장하여 다양한 보고서 작성 시나리오에 대응할 수 있도록 한다.

본 애플리케이션은 윈도우 전용 설치형으로, 서버-클라이언트 구조로 운영된다. 서버는 중앙 DB와 LLM 자원을 관리하고, 클라이언트는 Tauri + React + TypeScript 기반 데스크톱 UI를 제공한다. 프로필 데이터는 서버의 중앙 DB에 저장되며, 클라이언트는 서버 API를 통해 프로필을 관리한다. 서버 연결이 끊어진 상태에서도 로컬 캐시를 통해 읽기 전용으로 프로필 목록 조회가 가능해야 한다.

## Glossary

- **Profile_Manager**: 환경설정 프로필의 생성, 수정, 삭제, 복사, 내보내기, 가져오기를 관리하는 시스템 컴포넌트
- **Profile**: 현장별·양식별·발주처별 보고서 생성 기준정보를 담는 설정 단위 (서버 DB의 settings_profile 테이블 레코드)
- **Default_Profile**: 여러 프로필 중 기본으로 사용되는 프로필. 시스템에 하나만 존재할 수 있음
- **Profile_Name**: 프로필을 식별하기 위한 고유 이름 (필수 입력값, 1~50자)
- **Profile_Description**: 프로필의 용도나 특성을 설명하는 선택적 텍스트 (최대 200자)
- **Export_File**: 프로필 정보를 JSON 형식으로 내보낸 파일
- **Import_File**: 외부에서 가져오는 JSON 형식의 프로필 파일
- **Settings_Screen**: 환경설정 화면. 첫 번째 탭이 프로필 관리 영역임
- **Server**: 중앙 DB, LLM 엔진, 서버 발견 서비스를 실행하는 서버 인스턴스
- **Server_ID**: 서버를 고유하게 식별하는 UUID v4. IP 변경과 무관하게 서버를 식별함
- **Client**: Tauri 기반 데스크톱 UI 애플리케이션. 서버 API를 호출하여 데이터를 관리함

## Requirements

### Requirement 1: 프로필 생성

**User Story:** As a CM단 문서 담당자, I want 현장별·양식별로 여러 개의 설정 프로필을 생성할 수 있도록, so that 다양한 보고서 작성 시나리오에 대응할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 프로필 생성을 요청하고 공백을 제거한 후 1자 이상 50자 이하이며 기존 프로필명과 중복되지 않는 Profile_Name을 입력하면, THE Profile_Manager SHALL 새로운 Profile을 생성하고 SQLite 데이터베이스에 저장한다.
2. WHEN 프로필이 생성되면, THE Profile_Manager SHALL created_at 필드에 현재 시각을 자동으로 기록한다.
3. WHEN 프로필이 생성되면, THE Profile_Manager SHALL updated_at 필드에 현재 시각을 자동으로 기록한다.
4. IF 사용자가 Profile_Name을 입력하지 않거나 공백만 입력하고 생성을 요청하면, THEN THE Profile_Manager SHALL 프로필명이 필수 입력값임을 나타내는 오류 메시지를 표시하고 프로필을 생성하지 않는다.
5. IF 사용자가 입력한 Profile_Name이 기존 프로필명과 앞뒤 공백 제거 후 동일하면, THEN THE Profile_Manager SHALL 동일한 이름의 프로필이 이미 존재함을 나타내는 오류 메시지를 표시하고 프로필을 생성하지 않는다.
6. WHEN 시스템에 프로필이 하나도 없는 상태에서 첫 번째 프로필이 생성되면, THE Profile_Manager SHALL 해당 프로필을 Default_Profile로 자동 지정한다.
7. IF 사용자가 입력한 Profile_Name이 공백 제거 후 50자를 초과하면, THEN THE Profile_Manager SHALL 프로필명이 50자를 초과했음을 나타내는 오류 메시지를 표시하고 프로필을 생성하지 않는다.
8. WHEN 프로필이 성공적으로 생성되면, THE Profile_Manager SHALL 생성 완료를 나타내는 알림을 사용자에게 표시한다.

### Requirement 2: 프로필 수정

**User Story:** As a CM단 문서 담당자, I want 기존 프로필의 이름과 설명을 수정할 수 있도록, so that 변경된 현장 상황이나 보고서 요건을 반영할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 기존 Profile의 Profile_Name 또는 Profile_Description을 변경하고 저장을 요청하면, THE Profile_Manager SHALL 변경 사항을 SQLite 데이터베이스에 반영한다. 단, Profile_Name은 1자 이상 50자 이하, Profile_Description은 200자 이하여야 한다.
2. WHEN 프로필이 수정되면, THE Profile_Manager SHALL updated_at 필드를 현재 시각으로 갱신한다.
3. IF 사용자가 수정 시 Profile_Name을 빈 문자열 또는 공백만으로 구성된 값으로 변경하면, THEN THE Profile_Manager SHALL 프로필명이 필수 입력값임을 나타내는 오류 메시지를 표시하고 변경 사항을 저장하지 않는다.
4. IF 사용자가 수정 시 다른 프로필과 대소문자 무관하게 동일한 Profile_Name으로 변경하면, THEN THE Profile_Manager SHALL 동일한 이름의 프로필이 이미 존재함을 나타내는 오류 메시지를 표시하고 변경 사항을 저장하지 않는다.
5. IF 사용자가 존재하지 않는 Profile에 대해 수정을 요청하면, THEN THE Profile_Manager SHALL 해당 프로필을 찾을 수 없음을 나타내는 오류 메시지를 표시하고 어떠한 데이터도 변경하지 않는다.
6. IF 사용자가 Profile_Name을 51자 이상 또는 Profile_Description을 201자 이상으로 입력하면, THEN THE Profile_Manager SHALL 입력 길이 초과를 나타내는 오류 메시지를 표시하고 변경 사항을 저장하지 않는다.

### Requirement 3: 프로필 복사

**User Story:** As a CM단 문서 담당자, I want 기존 프로필을 복사하여 새 프로필을 만들 수 있도록, so that 유사한 설정을 빠르게 재사용할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 기존 Profile의 복사를 요청하면, THE Profile_Manager SHALL 원본 Profile의 Profile_Description 및 해당 Profile에 연결된 모든 환경설정(템플릿 매핑, 문서 샘플 설정, 폴더 설정, 대장/사진대지 설정, 저장위치/파일명 규칙)을 복사한 새로운 Profile을 생성한다.
2. WHEN 프로필이 복사되면, THE Profile_Manager SHALL 복사본의 Profile_Name을 "원본이름 (복사본)" 형식으로 자동 설정한다.
3. WHEN 프로필이 복사되면, THE Profile_Manager SHALL 복사본의 created_at과 updated_at을 현재 시각으로 설정한다.
4. WHEN 프로필이 복사되면, THE Profile_Manager SHALL 복사본의 is_default를 false로 설정한다.
5. IF "원본이름 (복사본)" 이름이 이미 존재하면, THEN THE Profile_Manager SHALL "원본이름 (복사본 2)", "원본이름 (복사본 3)" 순으로 최대 99까지 순번을 증가시켜 중복되지 않는 이름을 자동 생성한다.
6. IF 복사 대상 원본 Profile이 존재하지 않거나 복사 작업 중 오류가 발생하면, THEN THE Profile_Manager SHALL 복사 작업을 중단하고, 부분적으로 생성된 데이터를 롤백하며, 실패 원인을 나타내는 오류 메시지를 사용자에게 표시한다.

### Requirement 4: 프로필 삭제

**User Story:** As a CM단 문서 담당자, I want 불필요한 프로필을 삭제할 수 있도록, so that 프로필 목록을 깔끔하게 관리할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 프로필 삭제를 요청하면, THE Profile_Manager SHALL "프로필 '[프로필명]'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."라는 확인 대화상자를 표시한다.
2. WHEN 사용자가 삭제 확인을 승인하면, THE Profile_Manager SHALL 해당 Profile과 연결된 모든 하위 데이터(report_template, document_type_config, document_sample, folder_config, template_mapping)를 포함하여 SQLite 데이터베이스에서 영구 삭제한다.
3. IF 사용자가 삭제 확인 대화상자에서 취소를 선택하면, THEN THE Profile_Manager SHALL 삭제를 수행하지 않고 프로필 목록 화면을 현재 상태 그대로 유지한다.
4. IF 삭제 대상이 Default_Profile이고 다른 프로필이 존재하면, THEN THE Profile_Manager SHALL 가장 최근에 수정된(updated_at 기준) 다른 프로필을 새로운 Default_Profile로 자동 지정한다.
5. IF 시스템에 프로필이 하나만 존재하는 상태에서 삭제를 요청하면, THEN THE Profile_Manager SHALL "최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다."라는 오류 메시지를 표시한다.
6. WHEN 프로필 삭제가 완료되면, THE Profile_Manager SHALL 삭제된 프로필명을 포함한 삭제 완료 메시지를 표시하고 프로필 목록에서 해당 항목을 즉시 제거한다.

### Requirement 5: 기본 프로필 지정

**User Story:** As a CM단 문서 담당자, I want 특정 프로필을 기본 프로필로 지정할 수 있도록, so that 자동취합 실행 시 별도의 선택 없이 해당 프로필이 적용된다.

#### Acceptance Criteria

1. WHEN 사용자가 특정 Profile을 Default_Profile로 지정하면, THE Profile_Manager SHALL 해당 Profile의 is_default를 true로 설정하고, 기존 Default_Profile이 존재하는 경우 해당 Profile의 is_default를 false로 변경한다.
2. THE Profile_Manager SHALL 시스템 내에 Default_Profile을 정확히 하나만 유지한다.
3. WHEN 기본 프로필이 변경되면, THE Profile_Manager SHALL 새로 지정된 Default_Profile과 기존 Default_Profile 양쪽 모두의 updated_at을 현재 시각으로 갱신한다.
4. WHEN 시스템에 첫 번째 Profile이 생성되면, THE Profile_Manager SHALL 해당 Profile을 자동으로 Default_Profile로 지정한다.
5. WHEN 자동취합 실행 시 사용자가 적용 프로필을 별도로 선택하지 않으면, THE System SHALL Default_Profile로 지정된 프로필을 자동취합에 적용한다.

### Requirement 6: 프로필 내보내기

**User Story:** As a CM단 문서 담당자, I want 프로필을 JSON 파일로 내보낼 수 있도록, so that 다른 PC로 설정을 이전하거나 백업할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 프로필 내보내기를 요청하면, THE Profile_Manager SHALL 해당 Profile의 name, description, is_default, created_at, updated_at 정보와 해당 프로필에 연결된 document_type_config, folder_config, template_mapping 설정을 포함한 UTF-8 인코딩의 JSON 형식 Export_File을 생성한다.
2. WHEN 내보내기를 실행하면, THE Profile_Manager SHALL 사용자에게 파일 저장 위치를 선택할 수 있는 파일 저장 대화상자를 표시한다.
3. WHEN Export_File이 생성되면, THE Profile_Manager SHALL 파일명을 "profile_[프로필명]_[YYYYMMDD].json" 형식으로 기본 제안하되, 프로필명에 포함된 파일시스템 금지 문자(\ / : * ? " < > |)는 언더스코어(_)로 치환한다.
4. IF 내보내기 중 파일 저장에 실패하면, THEN THE Profile_Manager SHALL 저장 실패 원인(쓰기 권한 부족, 디스크 용량 부족 등)과 조치 방법을 포함한 오류 메시지를 표시하고, 사용자가 다른 저장 위치를 다시 선택할 수 있도록 파일 저장 대화상자를 유지한다.
5. WHEN Export_File 저장이 완료되면, THE Profile_Manager SHALL 저장된 파일의 전체 경로를 포함한 내보내기 완료 알림을 사용자에게 표시한다.

### Requirement 7: 프로필 가져오기

**User Story:** As a CM단 문서 담당자, I want JSON 파일에서 프로필을 가져올 수 있도록, so that 다른 PC에서 내보낸 설정을 현재 PC에 적용할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 프로필 가져오기를 요청하면, THE Profile_Manager SHALL 파일 선택 대화상자를 표시하되, 확장자 필터를 .json으로 제한하여 JSON 파일만 선택할 수 있도록 한다.
2. WHEN 유효한 Import_File이 선택되면, THE Profile_Manager SHALL 파일 내용을 파싱하여 name, description, is_default 및 프로필에 포함된 하위 설정 데이터를 읽어 새로운 Profile을 생성하고, id는 시스템이 새로 부여한다.
3. IF Import_File의 JSON 형식이 유효하지 않으면, THEN THE Profile_Manager SHALL JSON 파싱 실패를 나타내는 오류 메시지를 표시하고, 프로필을 생성하지 않는다.
4. IF Import_File에 필수 필드(name)가 누락되어 있으면, THEN THE Profile_Manager SHALL 필수 항목 누락을 나타내는 오류 메시지를 표시하고, 프로필을 생성하지 않는다.
5. IF 가져온 Profile_Name이 이미 존재하면, THEN THE Profile_Manager SHALL 이름 변경 확인 대화상자를 표시하고, 사용자가 새 이름을 입력하면 해당 이름으로 프로필을 생성하며, 사용자가 취소하면 가져오기를 중단하고 프로필을 생성하지 않는다.
6. WHEN 프로필을 가져오면, THE Profile_Manager SHALL created_at과 updated_at을 현재 시각으로 새로 설정한다.
7. IF Import_File의 is_default 값이 true이고 현재 시스템에 기본 프로필이 이미 존재하면, THEN THE Profile_Manager SHALL 가져온 프로필의 is_default를 false로 설정하여 기존 기본 프로필을 유지한다.
8. IF Import_File의 크기가 10MB를 초과하면, THEN THE Profile_Manager SHALL 파일 크기 초과를 나타내는 오류 메시지를 표시하고, 프로필을 생성하지 않는다.

### Requirement 8: 프로필 목록 조회

**User Story:** As a CM단 문서 담당자, I want 등록된 모든 프로필 목록을 한눈에 볼 수 있도록, so that 원하는 프로필을 빠르게 찾아 선택할 수 있다.

#### Acceptance Criteria

1. WHEN 사용자가 Settings_Screen의 프로필 탭을 열면, THE Profile_Manager SHALL 등록된 모든 Profile의 목록을 표시한다.
2. THE Profile_Manager SHALL 프로필 목록에 각 Profile의 name, description(최대 100자까지 표시, 초과 시 말줄임 처리), is_default, updated_at 정보를 표시한다.
3. THE Profile_Manager SHALL Default_Profile을 목록 최상단에 기본 프로필임을 나타내는 라벨 또는 아이콘을 부착하여 일반 프로필과 구분하여 표시한다.
4. THE Profile_Manager SHALL Default_Profile을 제외한 나머지 프로필을 updated_at 내림차순으로 정렬하여 표시한다.
5. IF 등록된 프로필이 없으면, THEN THE Profile_Manager SHALL 프로필이 없음을 안내하고 새 프로필 생성을 유도하는 메시지를 표시한다.
6. WHEN 사용자가 목록에서 특정 프로필 항목을 선택하면, THE Profile_Manager SHALL 해당 프로필의 상세 정보 화면으로 이동한다.
7. IF 프로필 목록 로드에 실패하면, THEN THE Profile_Manager SHALL 로드 실패 원인을 포함한 오류 메시지를 표시하고 재시도 수단을 제공한다.

### Requirement 9: 네트워크 내 독립 동작 및 서버 연결 관리

**User Story:** As a 현장 CM 관리자, I want 동일 네트워크망 내에서 서버와 연결하여 프로필을 관리하되, 서버 연결이 일시적으로 끊어져도 기본적인 프로필 조회가 가능하도록, so that 네트워크 불안정한 현장에서도 업무 중단 없이 작업할 수 있다.

#### Acceptance Criteria

1. THE Profile_Manager SHALL 프로필 데이터를 서버의 중앙 DB에 저장하고, 클라이언트는 서버 API를 통해 조회·수정한다.
2. THE Client SHALL 서버에서 조회한 프로필 목록을 로컬에 캐시하여, 서버 연결이 끊어져도 읽기 전용으로 프로필 목록을 표시한다.
3. IF 서버 연결이 끊어진 상태에서 프로필 생성·수정·삭제를 시도하면, THEN THE Client SHALL "서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요."라는 오류 메시지를 표시하고 해당 작업을 수행하지 않는다.
4. THE Client SHALL 외부 인터넷으로의 아웃바운드 네트워크 요청을 수행하지 않으며, 오직 동일 네트워크망 내 서버와만 통신한다.
5. IF 서버 연결이 복구되면, THEN THE Client SHALL 자동으로 프로필 목록을 최신 상태로 갱신한다.

### Requirement 10: 데이터 직렬화 라운드트립

**User Story:** As a CM단 문서 담당자, I want 프로필을 내보내고 다시 가져왔을 때 데이터가 동일하게 유지되도록, so that 설정 이전 시 데이터 손실이 없다.

#### Acceptance Criteria

1. WHEN 유효한 Profile 객체를 내보내기 후 가져오기를 수행했을 때, THE Profile_Manager SHALL 원본의 name, description, is_default 필드 값을 바이트 단위로 동일하게 복원한다.
2. THE Profile_Manager SHALL Export_File의 JSON 구조에 name, description, is_default 필드를 포함하고, UTF-8 인코딩으로 저장한다.
3. WHEN Import_File을 파싱할 때, THE Profile_Manager SHALL UTF-8 인코딩된 JSON 파일을 읽어 name, description, is_default 필드를 추출하고 Profile 객체를 생성한다.
4. IF Import_File이 유효한 JSON 형식이 아니거나 필수 필드(name)가 누락된 경우, THEN THE Profile_Manager SHALL 가져오기를 중단하고 파싱 실패 원인을 포함한 오류 메시지를 표시하며, 기존 프로필 데이터를 변경하지 않는다.
5. IF 가져오기 대상 프로필의 name이 기존 프로필과 동일한 경우, THEN THE Profile_Manager SHALL 덮어쓰기 또는 새 이름으로 저장 중 사용자에게 선택을 요청한다.
