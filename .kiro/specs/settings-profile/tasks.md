# Implementation Plan: 환경설정 프로필 관리 (settings-profile)

## Overview

서버-클라이언트 아키텍처 기반의 환경설정 프로필 관리 기능을 구현한다. 서버(Python FastAPI + SQLite + mDNS)는 중앙 DB와 비즈니스 로직을 담당하고, 클라이언트(Tauri + React + TypeScript)는 서버 API를 호출하여 UI를 제공한다. mDNS 기반 서버 발견, Server-ID 인증, 로컬 캐시 기반 오프라인 읽기를 지원한다.

## Tasks

- [x] 1. 서버 프로젝트 초기 설정
  - [x] 1.1 FastAPI 프로젝트 구조 및 의존성 설정
    - `server/` 디렉토리 하위에 FastAPI 프로젝트 생성
    - `pyproject.toml` 또는 `requirements.txt`에 의존성 정의 (fastapi, uvicorn, sqlalchemy, pydantic, alembic, zeroconf, hypothesis, pytest)
    - `app/` 패키지 구조 생성 (main.py, routers/, services/, repositories/, models/, schemas/, core/)
    - `app/main.py`에 FastAPI 앱 인스턴스 생성 및 라우터 등록
    - uvicorn 실행 설정 (host="0.0.0.0", port=8741)
    - _Requirements: 9.1, 9.4_

  - [x] 1.2 SQLite 데이터베이스 및 SQLAlchemy 설정
    - `app/core/database.py`에 SQLAlchemy async engine 및 session factory 설정
    - `app/models/settings_profile.py`에 SettingsProfile ORM 모델 정의
    - Alembic 초기화 및 마이그레이션 설정
    - `settings_profile` 테이블 마이그레이션 작성 (id, name, description, is_default, created_at, updated_at)
    - 인덱스 생성 (idx_profile_name UNIQUE, idx_profile_is_default, idx_profile_updated_at)
    - _Requirements: 1.1, 9.1_

  - [x] 1.3 Server-ID 생성 및 관리 모듈
    - `app/core/server_identity.py`에 Server-ID (UUID v4) 생성 및 영속화 로직 구현
    - 서버 최초 실행 시 UUID v4 생성 후 로컬 파일(`server_id.json`)에 저장
    - 이후 실행 시 기존 Server-ID 로드
    - _Requirements: 9.1_

  - [x] 1.4 mDNS Advertiser 구현
    - `app/core/mdns_advertiser.py`에 zeroconf 라이브러리 기반 mDNS 서비스 광고 구현
    - 서비스 타입: `_cm-report-server._tcp.local.`
    - 서비스 속성: Server-ID, 포트, 버전 정보 제공
    - 서버 시작 시 등록, 종료 시 해제
    - 동일 네트워크 내 기존 서버 존재 여부 확인 (중복 방지)
    - _Requirements: 9.1, 9.4_

- [x] 2. 클라이언트 프로젝트 초기 설정
  - [x] 2.1 Tauri + React + TypeScript 프로젝트 구조 설정
    - `client/` 디렉토리 하위에 Tauri v2 + React + TypeScript 프로젝트 구조 생성
    - `package.json`에 의존성 정의 (react, zustand, @tauri-apps/api, @tauri-apps/plugin-dialog, vitest, @testing-library/react)
    - `src/` 하위 디렉토리 구조 (pages/, components/, stores/, api/, types/, cache/)
    - TypeScript 인터페이스 정의 (`src/types/profile.ts`: Profile, ProfileCreateInput, ProfileUpdateInput, ProfileListResponse)
    - _Requirements: 9.1_

  - [x] 2.2 mDNS Discovery 클라이언트 구현
    - Tauri 사이드카 또는 Rust 플러그인으로 mDNS 탐색 구현
    - `_cm-report-server._tcp.local.` 서비스 검색
    - 발견된 서버의 IP, 포트, Server-ID 추출
    - 서버 발견 결과를 React 앱으로 전달하는 IPC 브릿지 구현
    - _Requirements: 9.1, 9.4_

  - [x] 2.3 서버 연결 상태 관리 모듈
    - `src/stores/connectionStore.ts`에 서버 연결 상태 Zustand store 구현
    - 상태: connected, disconnected, connecting
    - 주기적 health check (ping) 구현
    - 연결 끊김/복구 이벤트 핸들링
    - _Requirements: 9.2, 9.3, 9.5_

- [x] 3. 서버 인증 미들웨어
  - [x] 3.1 Server-ID 토큰 인증 미들웨어 구현
    - `app/core/auth.py`에 FastAPI dependency로 Server-ID 토큰 검증 로직 구현
    - 요청 헤더에서 `X-Server-ID` 토큰 추출 및 검증
    - 유효하지 않은 토큰 시 401 Unauthorized 반환
    - 모든 `/api/v1/` 라우터에 인증 dependency 적용
    - _Requirements: 9.1, 9.4_

- [x] 4. Checkpoint - 서버/클라이언트 기반 구조 확인
  - 서버 FastAPI 앱이 정상 시작되는지 확인
  - mDNS advertiser/discoverer 동작 확인
  - Server-ID 토큰 인증 미들웨어 동작 확인
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. 서버 데이터 모델 및 Pydantic 스키마
  - [x] 5.1 Pydantic 요청/응답 스키마 정의
    - `app/schemas/profile.py`에 ProfileCreate, ProfileUpdate, ProfileResponse, ProfileListResponse, ErrorResponse 정의
    - ProfileCreate: name(1~50자 검증, strip), description(0~200자)
    - ProfileUpdate: name(Optional, 1~50자), description(Optional, 0~200자)
    - ProfileResponse: id, name, description, is_default, created_at, updated_at
    - ErrorResponse: error_code, message, detail, field
    - field_validator로 공백 제거 및 길이 검증
    - _Requirements: 1.1, 1.4, 1.7, 2.1, 2.3, 2.6_

- [x] 6. Repository 레이어 구현
  - [x] 6.1 ProfileRepository 구현
    - `app/repositories/profile_repository.py`에 CRUD 메서드 구현
    - `create(profile)`: 프로필 삽입
    - `get_by_id(id)`: ID로 조회
    - `get_by_name(name)`: 이름으로 조회 (대소문자 무관)
    - `get_default()`: 기본 프로필 조회
    - `list_all()`: 전체 목록 조회
    - `update(profile)`: 프로필 업데이트
    - `delete(id)`: 프로필 삭제
    - `count()`: 프로필 수 조회
    - `get_latest_updated()`: 가장 최근 수정된 프로필 조회
    - _Requirements: 1.1, 2.1, 4.2, 8.1_

- [x] 7. Service 레이어 구현
  - [x] 7.1 ProfileService - 생성, 수정, 삭제 로직
    - `app/services/profile_service.py`에 비즈니스 로직 구현
    - `create_profile`: 이름 중복 검사 (대소문자 무관), 첫 프로필 자동 기본 지정, 타임스탬프 설정
    - `update_profile`: 존재 확인, 이름 중복 검사 (자기 자신 제외), updated_at 갱신
    - `delete_profile`: 존재 확인, 마지막 프로필 삭제 방지, 기본 프로필 삭제 시 위임 (가장 최근 수정된 프로필), 하위 데이터 cascade 삭제, 트랜잭션 처리
    - _Requirements: 1.1~1.8, 2.1~2.6, 4.1~4.6_

  - [x] 7.2 ProfileService - 복사, 기본 프로필 지정 로직
    - `copy_profile`: 원본 조회, description 및 하위 설정 복사, 이름 생성 ("원본 (복사본)", 순번 증가 최대 99), is_default=false, 롤백 처리
    - `set_default_profile`: 기존 기본 해제 + 새 기본 설정 단일 트랜잭션, 양쪽 updated_at 갱신
    - _Requirements: 3.1~3.6, 5.1~5.4_

  - [x] 7.3 ProfileService - 내보내기/가져오기 로직
    - `export_profile`: 프로필 + 하위 설정(document_type_config, folder_config, template_mapping) JSON 직렬화, UTF-8
    - `import_profile`: JSON 파싱, 필수 필드 검증(name), 크기 검증(10MB), is_default 처리 (기존 기본 있으면 false), 타임스탬프 재설정
    - 파일명 생성 유틸: 금지문자(\ / : * ? " < > |) → 언더스코어 치환
    - _Requirements: 6.1~6.5, 7.1~7.8, 10.1~10.5_

  - [x] 7.4 ProfileService - 목록 조회 로직
    - `list_profiles`: 기본 프로필 최상단 + 나머지 updated_at 내림차순 정렬
    - _Requirements: 8.1~8.7_

- [x] 8. API Router 구현
  - [x] 8.1 프로필 CRUD API 엔드포인트 구현
    - `app/routers/profile_router.py`에 FastAPI 라우터 구현
    - `GET /api/v1/profiles`: 목록 조회
    - `POST /api/v1/profiles`: 프로필 생성
    - `GET /api/v1/profiles/{profile_id}`: 상세 조회
    - `PUT /api/v1/profiles/{profile_id}`: 프로필 수정
    - `DELETE /api/v1/profiles/{profile_id}`: 프로필 삭제
    - 에러 응답 매핑 (422, 409, 404, 400, 500)
    - _Requirements: 1.1~1.8, 2.1~2.6, 4.1~4.6, 8.1~8.7_

  - [x] 8.2 프로필 복사, 기본 지정, 내보내기/가져오기 API 엔드포인트
    - `POST /api/v1/profiles/{profile_id}/copy`: 복사
    - `PUT /api/v1/profiles/{profile_id}/default`: 기본 프로필 지정
    - `GET /api/v1/profiles/{profile_id}/export`: 내보내기 (JSON 응답)
    - `POST /api/v1/profiles/import`: 가져오기 (JSON 업로드, 10MB 제한)
    - _Requirements: 3.1~3.6, 5.1~5.4, 6.1~6.5, 7.1~7.8_

- [x] 9. Checkpoint - 서버 API 동작 확인
  - FastAPI TestClient로 전체 API 엔드포인트 호출 테스트
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. 클라이언트 API Client 구현
  - [x] 10.1 서버 REST API 호출 클라이언트
    - `src/api/profileApi.ts`에 fetch 기반 API 클라이언트 구현
    - 모든 요청에 `X-Server-ID` 토큰 헤더 포함
    - 메서드: fetchProfiles, createProfile, updateProfile, deleteProfile, copyProfile, setDefaultProfile, exportProfile, importProfile
    - HTTP 에러 응답 파싱 및 에러 코드/메시지 추출
    - 네트워크 오류 감지 (서버 연결 끊김 판별)
    - _Requirements: 9.1, 9.3_

- [x] 11. 클라이언트 로컬 캐시 구현
  - [x] 11.1 로컬 캐시 저장소 구현
    - `src/cache/profileCache.ts`에 IndexedDB 또는 로컬 JSON 파일 기반 캐시 구현
    - API 응답 성공 시 프로필 목록을 로컬에 캐시
    - 서버 연결 끊김 시 캐시된 데이터로 읽기 전용 목록 제공
    - 서버 연결 복구 시 캐시 갱신
    - _Requirements: 9.2, 9.5_

- [x] 12. 클라이언트 상태 관리 (Zustand Store)
  - [x] 12.1 ProfileStore 구현
    - `src/stores/profileStore.ts`에 Zustand store 구현
    - 상태: profiles, selectedProfileId, isLoading, error
    - 액션: fetchProfiles, createProfile, updateProfile, deleteProfile, copyProfile, setDefaultProfile, exportProfile, importProfile
    - 서버 연결 상태에 따라 캐시 fallback 분기
    - 쓰기 작업 시 서버 연결 끊김이면 에러 메시지 표시 및 작업 차단
    - _Requirements: 9.2, 9.3, 9.5_

- [x] 13. Frontend 컴포넌트 구현
  - [x] 13.1 프로필 목록 컴포넌트
    - `src/components/ProfileList.tsx`: 프로필 목록 렌더링
    - `src/components/ProfileListItem.tsx`: 개별 항목 (이름, 설명 100자 말줄임, 기본 배지, 수정일)
    - `src/components/EmptyProfileState.tsx`: 빈 목록 안내 및 생성 유도 메시지
    - 기본 프로필 최상단 표시, 나머지 updated_at 내림차순 정렬
    - 항목 선택 시 상세 정보 패널로 이동
    - _Requirements: 8.1~8.7_

  - [x] 13.2 프로필 생성/수정 폼 컴포넌트
    - `src/components/ProfileForm.tsx`: 생성/수정 공용 폼
    - 입력 필드: name (필수, 1~50자), description (선택, 0~200자)
    - 실시간 유효성 검증 및 에러 메시지 표시
    - 성공 시 알림 토스트 표시
    - _Requirements: 1.1~1.8, 2.1~2.6_

  - [x] 13.3 프로필 액션 및 대화상자 컴포넌트
    - `src/components/ProfileActions.tsx`: 복사, 내보내기, 삭제 버튼 그룹
    - `src/components/DeleteConfirmDialog.tsx`: 삭제 확인 대화상자 ("프로필 '[이름]'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
    - `src/components/ImportDialog.tsx`: 가져오기 시 이름 충돌 해결 대화상자
    - Tauri dialog API 연동 (파일 열기/저장 대화상자)
    - _Requirements: 4.1~4.6, 6.1~6.5, 7.1~7.8_

  - [x] 13.4 서버 연결 상태 표시 컴포넌트
    - `src/components/ConnectionStatus.tsx`: 서버 연결 상태 표시 (connected/disconnected 아이콘 + 텍스트)
    - 연결 끊김 시 상단 배너로 경고 메시지 표시
    - 쓰기 작업 버튼 비활성화 (서버 연결 끊김 시)
    - _Requirements: 9.2, 9.3, 9.5_

  - [x] 13.5 Settings 페이지 및 라우팅 통합
    - `src/pages/SettingsPage.tsx`: 환경설정 메인 페이지 (탭 구조)
    - 첫 번째 탭: 프로필 관리 (ProfileTab)
    - 모든 컴포넌트 조립 및 데이터 플로우 연결
    - 에러 경계 (ErrorBoundary) 적용
    - _Requirements: 8.1, 8.6_

- [x] 14. Checkpoint - 프론트엔드-서버 연동 확인
  - 클라이언트에서 서버 API 호출이 정상 동작하는지 확인
  - mDNS 서버 발견 → 연결 → CRUD 플로우 동작 확인
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. 에러 처리 및 사용자 피드백
  - [x] 15.1 서버 에러 핸들러 구현
    - `app/core/exceptions.py`에 커스텀 예외 클래스 정의 (ProfileNotFoundError, ProfileNameDuplicateError, LastProfileDeleteError, ImportValidationError 등)
    - `app/core/error_handlers.py`에 FastAPI exception handler 등록
    - 에러 코드 → HTTP 상태 코드 매핑 (ErrorCodes 클래스)
    - _Requirements: 1.4, 1.5, 1.7, 2.3~2.6, 4.5, 7.3, 7.4, 7.8_

  - [x] 15.2 클라이언트 에러 처리 및 토스트 알림
    - `src/utils/errorMessages.ts`에 에러 코드 → 한국어 메시지 매핑
    - 토스트/스낵바 컴포넌트로 성공/실패 알림 표시
    - 서버 연결 오류 시 "서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요." 메시지 표시
    - 목록 로드 실패 시 재시도 버튼 제공
    - _Requirements: 1.8, 4.6, 6.4, 6.5, 7.3~7.5, 8.7, 9.3_

- [x] 16. Property-Based 테스트 구현
  - [x] 16.1 Property 1: 프로필 생성 라운드트립 테스트
    - **Property 1: 프로필 생성 라운드트립**
    - Hypothesis로 유효한 이름(1~50자) + 설명(0~200자) 생성기 작성
    - 생성 후 조회 시 name, description 일치 검증
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 16.2 Property 2: 프로필 수정 라운드트립 테스트
    - **Property 2: 프로필 수정 라운드트립**
    - 기존 프로필에 대해 유효한 수정 입력 생성기 작성
    - 수정 후 조회 시 변경 값 일치 및 updated_at 갱신 검증
    - **Validates: Requirements 2.1, 2.2**

  - [x] 16.3 Property 3: 이름 유효성 검증 테스트
    - **Property 3: 이름 유효성 검증 — 공백 및 길이 초과 거부**
    - 공백 문자열 및 51자 이상 문자열 생성기 작성
    - 생성/수정 시 거부 및 데이터 무변경 검증
    - **Validates: Requirements 1.4, 1.7, 2.3, 2.6**

  - [x] 16.4 Property 4: 이름 유니크 제약 테스트
    - **Property 4: 이름 유니크 제약**
    - 동일 이름 대소문자 변형 생성기 작성
    - 중복 생성/수정 시 거부 검증
    - **Validates: Requirements 1.5, 2.4**

  - [x] 16.5 Property 5: 기본 프로필 단일성 불변식 테스트
    - **Property 5: 기본 프로필 단일성 불변식**
    - 임의의 작업 시퀀스(생성, 수정, 삭제, 복사, 기본 지정) 생성기 작성
    - 모든 작업 후 is_default=true 프로필이 정확히 1개인지 검증
    - **Validates: Requirements 5.1, 5.2, 5.3, 1.6, 4.4**

  - [x] 16.6 Property 6: 프로필 복사 속성 일관성 테스트
    - **Property 6: 프로필 복사 속성 일관성**
    - 임의의 유효 프로필 생성 후 복사
    - 복사본 description=원본, is_default=false, 이름 형식 검증
    - **Validates: Requirements 3.2, 3.3, 3.4**

  - [x] 16.7 Property 7: 복사본 이름 순번 증가 테스트
    - **Property 7: 복사본 이름 순번 증가**
    - N번(2~10) 연속 복사 시 이름 고유성 및 순번 패턴 검증
    - **Validates: Requirements 3.5**

  - [x] 16.8 Property 8: 기본 프로필 삭제 시 위임 테스트
    - **Property 8: 기본 프로필 삭제 시 위임**
    - 2~10개 프로필 집합 생성, 기본 프로필 삭제 후 updated_at 최신 프로필이 기본 되는지 검증
    - **Validates: Requirements 4.4**

  - [x] 16.9 Property 9: 직렬화 라운드트립 테스트
    - **Property 9: 직렬화 라운드트립**
    - 임의의 유효 프로필 생성, export → import 후 name, description 바이트 동일 검증
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [x] 16.10 Property 10: 잘못된 JSON 가져오기 거부 테스트
    - **Property 10: 잘못된 JSON 가져오기 거부**
    - 랜덤 바이트열 및 필수 필드 누락 JSON 생성기 작성
    - 가져오기 거부 및 기존 데이터 무변경 검증
    - **Validates: Requirements 7.3, 7.4, 10.4**

  - [x] 16.11 Property 11: 내보내기 파일명 특수문자 치환 테스트
    - **Property 11: 내보내기 파일명 특수문자 치환**
    - 특수문자(\ / : * ? " < > |) 포함 이름 생성기 작성
    - 결과 파일명에 금지 문자 미포함 검증
    - **Validates: Requirements 6.3**

  - [x] 16.12 Property 12: 목록 정렬 불변식 테스트
    - **Property 12: 목록 정렬 불변식**
    - 1개 이상 프로필 집합 생성, 목록 조회 시 첫 항목=기본, 나머지 updated_at 내림차순 검증
    - **Validates: Requirements 8.3, 8.4**

- [x] 17. 단위 테스트 및 통합 테스트
  - [x] 17.1 서버 단위 테스트 (pytest)
    - 첫 번째 프로필 생성 시 자동 기본 지정 테스트 (Req 1.6)
    - 존재하지 않는 프로필 수정 시 404 반환 테스트 (Req 2.5)
    - 마지막 프로필 삭제 방지 테스트 (Req 4.5)
    - 기본 프로필 존재 시 is_default=true 가져오기 → false 처리 테스트 (Req 7.7)
    - 10MB 초과 파일 거부 테스트 (Req 7.8)
    - 빈 목록 조회 시 빈 배열 반환 테스트 (Req 8.5)
    - _Requirements: 1.6, 2.5, 4.5, 7.7, 7.8, 8.5_

  - [x] 17.2 서버 통합 테스트 (FastAPI TestClient)
    - 프로필 복사 시 하위 설정 데이터 포함 여부 테스트 (Req 3.1)
    - 프로필 삭제 시 cascade 동작 테스트 (Req 4.2)
    - 전체 CRUD 시나리오 flow 테스트
    - 에러 응답 형식 및 상태 코드 매핑 테스트
    - _Requirements: 3.1, 4.2, 전체 API_

  - [x] 17.3 프론트엔드 테스트 (Vitest + React Testing Library)
    - ProfileList 컴포넌트 렌더링 테스트
    - ProfileForm 유효성 검증 UI 피드백 테스트
    - DeleteConfirmDialog 확인/취소 동작 테스트
    - ConnectionStatus 상태별 표시 테스트
    - EmptyProfileState 렌더링 테스트
    - 에러 메시지 표시 테스트
    - _Requirements: 8.1~8.7, 9.2, 9.3_

- [x] 18. Final Checkpoint - 전체 기능 검증
  - 서버-클라이언트 전체 연동 동작 확인
  - mDNS 서버 발견 → 인증 → CRUD → 내보내기/가져오기 → 오프라인 캐시 전체 플로우 확인
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 서버(Python)와 클라이언트(TypeScript/React)는 별도 프로젝트로 관리됨
- 서버는 FastAPI + SQLAlchemy + SQLite, 클라이언트는 Tauri + React + Zustand 기반
- mDNS 서버 발견은 zeroconf(Python) 및 Tauri Rust 사이드카 기반
- Property 테스트는 Python Hypothesis 라이브러리 사용
- 프론트엔드 테스트는 Vitest + React Testing Library 사용
- 모든 통신은 동일 LAN 내 HTTP로 제한, 인터넷 아웃바운드 없음
- Checkpoints ensure incremental validation

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.2", "2.3"] },
    { "id": 2, "tasks": ["1.4", "3.1", "5.1"] },
    { "id": 3, "tasks": ["6.1"] },
    { "id": 4, "tasks": ["7.1", "7.2", "7.3", "7.4"] },
    { "id": 5, "tasks": ["8.1", "8.2", "15.1"] },
    { "id": 6, "tasks": ["10.1", "11.1"] },
    { "id": 7, "tasks": ["12.1", "15.2"] },
    { "id": 8, "tasks": ["13.1", "13.2", "13.3", "13.4"] },
    { "id": 9, "tasks": ["13.5"] },
    { "id": 10, "tasks": ["16.1", "16.2", "16.3", "16.4", "16.5", "16.6", "16.7", "16.8", "16.9", "16.10", "16.11", "16.12"] },
    { "id": 11, "tasks": ["17.1", "17.2", "17.3"] }
  ]
}
```
