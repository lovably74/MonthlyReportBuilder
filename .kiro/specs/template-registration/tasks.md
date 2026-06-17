# Implementation Plan: 월간보고서 HWPX 양식 등록 (template-registration)

## Overview

기존 settings-profile 패턴과 동일한 서버-클라이언트 레이어 구조를 따라 HWPX 양식 등록 기능을 구현한다. 서버(Python FastAPI)는 DB 모델, HWPX 파서, Repository, Service, Router 순으로 구축하고, 클라이언트(Tauri + React + TypeScript)는 타입 정의, API Client, Zustand Store, UI 컴포넌트 순으로 구현한다. 기존 SettingsPage에 "양식" 탭을 추가하여 통합한다.

## Tasks

- [ ] 1. 서버 DB 모델 및 마이그레이션
  - [ ] 1.1 ReportTemplate ORM 모델 및 Alembic 마이그레이션 생성
    - `app/models/report_template.py`에 ReportTemplate SQLAlchemy 모델 정의
    - 컬럼: id, profile_id(FK → settings_profile.id, CASCADE), original_file_name, stored_path, file_type, version, detected_tags(TEXT, JSON), created_at
    - 인덱스: idx_template_profile_id, idx_template_created_at
    - Alembic 마이그레이션 파일 생성 및 적용
    - _Requirements: 9.1, 9.4, 3.4, 10.1_

  - [ ] 1.2 Pydantic 스키마 정의
    - `app/schemas/template.py`에 DetectedTag, TemplateResponse, TemplateListResponse, TagUpdateRequest, SectionPreview, TemplatePreviewResponse 정의
    - DetectedTag: name, section, position, is_manual
    - TemplateResponse: id, profile_id, original_file_name, file_type, version, detected_tags, created_at
    - _Requirements: 3.3, 3.4, 10.1, 10.2_

- [ ] 2. 서버 HWPX 파서 모듈
  - [ ] 2.1 HwpxParser 구현
    - `app/services/hwpx_parser.py`에 HwpxParser 클래스 구현
    - `validate(file_bytes)`: ZIP 유효성, Contents/ 존재, section*.xml 존재, XML well-formed 검증
    - `detect_tags(file_bytes)`: KNOWN_TAGS 20개 + CUSTOM_TAG_PATTERN 정규식 매칭
    - `get_structure(file_bytes)`: 섹션 파일 목록 + 섹션별 태그 트리 반환
    - ValidationResult 타입 정의 (is_valid, error_code, error_message)
    - _Requirements: 2.1~2.7, 3.1~3.6_

  - [ ]* 2.2 Property 1: HWPX 유효성 검증 테스트
    - **Property 1: HWPX 유효성 검증 — 잘못된 파일 거부**
    - Hypothesis로 랜덤 바이트열, 불완전 ZIP, Contents/ 없는 ZIP, 잘못된 XML ZIP 생성기 작성
    - validate()가 각 유형에 맞는 에러를 반환하는지 검증
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

  - [ ]* 2.3 Property 2: 태그 탐지 완전성 테스트
    - **Property 2: 태그 탐지 완전성**
    - KNOWN_TAGS 랜덤 부분집합이 삽입된 section XML을 생성하는 Hypothesis 전략 작성
    - detect_tags() 결과가 삽입된 태그 수와 정확히 일치하는지 검증
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.5**

- [ ] 3. 서버 Repository + Service
  - [ ] 3.1 TemplateRepository 구현
    - `app/repositories/template_repository.py`에 CRUD 메서드 구현
    - create, get_by_id, list_by_profile, get_by_profile_and_filename, delete, update
    - list_by_profile은 created_at DESC 정렬
    - _Requirements: 6.3, 9.1, 9.2_

  - [ ] 3.2 TemplateService 구현
    - `app/services/template_service.py`에 비즈니스 로직 구현
    - upload_template: 파일 검증 → 태그 탐지 → 버전 결정 → 파일 저장 → DB 저장
    - list_templates, get_template, delete_template(DB + 물리 파일), update_tags, get_preview
    - 버전 관리: 동일 profile_id+original_file_name 존재 시 version+1, stored_path에 _v{N} 접미사
    - 태그 수정: 빈/공백 태그명 거부, 중복 태그명 거부
    - detected_tags JSON 파싱 실패 시 빈 배열 폴백
    - _Requirements: 1.3, 1.6, 3.4, 3.6, 4.2~4.6, 5.1~5.4, 8.2, 10.4_

  - [ ]* 3.3 Property 3: detected_tags JSON 라운드트립 테스트
    - **Property 3: detected_tags JSON 라운드트립**
    - 랜덤 DetectedTag 리스트(name, section, position, is_manual) 생성기 작성
    - JSON 직렬화 → 역직렬화 후 원본과 동일한지 검증
    - **Validates: Requirements 3.4, 10.1, 10.2, 10.3**

  - [ ]* 3.4 Property 4: 태그 편집 불변식 테스트
    - **Property 4: 태그 편집 불변식**
    - 랜덤 태그 목록 + 추가/삭제 작업 생성기 작성
    - 추가 시 길이+1, 삭제 시 길이-1, 다른 태그 불변 검증
    - **Validates: Requirements 4.2, 4.3**

  - [ ]* 3.5 Property 5: 태그명 유효성 검증 테스트
    - **Property 5: 태그명 유효성 검증**
    - 공백/빈 문자열 + 기존 태그명 중복 시도 생성기 작성
    - 거부 및 기존 목록 불변 검증
    - **Validates: Requirements 4.5, 4.6**

  - [ ]* 3.6 Property 6: 버전 증가 불변식 테스트
    - **Property 6: 버전 증가 불변식**
    - 동일 파일명 N회(1~10) 업로드 시뮬레이션
    - N개 레코드 존재, version 1~N 순차, stored_path 패턴 검증
    - **Validates: Requirements 5.1, 5.2, 5.4**

- [ ] 4. 서버 API Router
  - [ ] 4.1 Template Router 엔드포인트 구현
    - `app/routers/template_router.py`에 FastAPI 라우터 구현
    - POST /api/v1/templates: multipart/form-data 업로드 (profile_id 쿼리 파라미터, 100MB 제한)
    - GET /api/v1/templates: 프로필별 목록 조회
    - GET /api/v1/templates/{template_id}: 상세 조회
    - DELETE /api/v1/templates/{template_id}: 삭제
    - PUT /api/v1/templates/{template_id}/tags: 태그 매핑 수정
    - GET /api/v1/templates/{template_id}/preview: 구조 미리보기
    - 에러 응답 매핑 (400, 404, 413, 500)
    - `app/main.py`에 라우터 등록
    - _Requirements: 1.1~1.7, 4.4, 6.1, 6.4, 7.1, 8.1~8.5_

  - [ ]* 4.2 Property 7: 템플릿 목록 정렬 테스트
    - **Property 7: 템플릿 목록 정렬**
    - 랜덤 created_at 값을 가진 템플릿 집합 생성
    - list_templates() 결과가 created_at 내림차순인지 검증
    - **Validates: Requirements 6.3**

  - [ ]* 4.3 Property 8: 프로필 격리 테스트
    - **Property 8: 프로필 격리**
    - 2개 프로필 각각에 랜덤 템플릿 생성
    - list_templates(profile_id=A)에 profile_id=B 항목 미포함 검증
    - **Validates: Requirements 9.2**

- [ ] 5. Checkpoint - 서버 API 동작 확인
  - 서버 전체 템플릿 API 엔드포인트 호출 테스트
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. 클라이언트 타입 + API Client
  - [ ] 6.1 TypeScript 인터페이스 정의
    - `src/types/template.ts`에 DetectedTag, Template, TemplateListResponse, TagMapping, SectionPreview, TemplatePreview 인터페이스 정의
    - _Requirements: 3.3, 6.2, 7.1_

  - [ ] 6.2 Template API Client 구현
    - `src/api/templateApi.ts`에 fetch 기반 API 클라이언트 구현
    - uploadTemplate(profileId, file): multipart/form-data POST
    - listTemplates(profileId): GET
    - getTemplate(id): GET
    - deleteTemplate(id): DELETE
    - updateTags(id, tags): PUT
    - getPreview(id): GET
    - 모든 요청에 X-Server-ID 헤더 포함, 에러 응답 파싱
    - _Requirements: 1.2, 6.1, 6.4, 8.2_

- [ ] 7. 클라이언트 Store + 컴포넌트
  - [ ] 7.1 TemplateStore (Zustand) 구현
    - `src/stores/templateStore.ts`에 Zustand store 구현
    - 상태: templates, selectedTemplateId, isLoading, isUploading, error
    - 액션: fetchTemplates, uploadTemplate, deleteTemplate, updateTags, selectTemplate
    - 서버 연결 끊김 시 쓰기 작업 차단
    - _Requirements: 1.2, 1.4, 1.7, 6.1, 6.6, 8.4_

  - [ ] 7.2 TemplateTab + TemplateList 컴포넌트 구현
    - `src/pages/TemplateTab.tsx`: 양식 탭 컨테이너 (목록 + 업로드 버튼 + 상세)
    - `src/components/TemplateList.tsx`: 템플릿 목록 렌더링 (파일명, 버전, 태그 수, 생성일)
    - `src/components/TemplateListItem.tsx`: 개별 항목 컴포넌트
    - `src/components/EmptyTemplateState.tsx`: 빈 상태 안내 + 업로드 유도
    - _Requirements: 6.1~6.5_

  - [ ] 7.3 TemplateUploadButton + TemplateDetail 구현
    - `src/components/TemplateUploadButton.tsx`: 업로드 버튼 + .hwpx 확장자 필터 파일 대화상자
    - `src/components/TemplateDetail.tsx`: 상세 화면 (태그 목록 + 미리보기 + 삭제)
    - `src/components/TemplatePreview.tsx`: 섹션+태그 트리 구조 미리보기
    - _Requirements: 1.1, 1.2, 1.5, 7.1~7.4_

  - [ ] 7.4 TagEditor + DeleteTemplateDialog 구현
    - `src/components/TagEditor.tsx`: 태그 추가/삭제 편집 UI (자동/수동 태그 구분 표시)
    - `src/components/DeleteTemplateDialog.tsx`: 삭제 확인 대화상자
    - 에러 메시지 매핑 (`src/utils/errorMessages.ts`에 TEMPLATE_ERROR_MESSAGES 추가)
    - _Requirements: 4.1~4.7, 8.1~8.5_

- [ ] 8. Settings 페이지 통합 — "양식" 탭 추가
  - [ ] 8.1 SettingsPage에 양식 탭 통합
    - `src/pages/SettingsPage.tsx`의 TABS 배열에 `{ id: 'template', label: '양식' }` 추가
    - TemplateTab 컴포넌트 조건부 렌더링 연결
    - 프로필 전환 시 TemplateStore 목록 재조회 연동
    - _Requirements: 9.2, 6.1_

- [ ] 9. Checkpoint - 프론트엔드-서버 연동 확인
  - 클라이언트에서 템플릿 업로드 → 목록 조회 → 상세 → 태그 편집 → 삭제 플로우 확인
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. 테스트 (단위 + PBT + 통합)
  - [ ]* 10.1 Property 9: JSON 파싱 실패 시 안전한 폴백 테스트
    - **Property 9: JSON 파싱 실패 시 안전한 폴백**
    - 랜덤 비-JSON 문자열을 detected_tags 컬럼에 직접 삽입
    - 템플릿 조회 시 예외 없이 빈 태그 목록 반환 검증
    - **Validates: Requirements 10.4**

  - [ ]* 10.2 서버 단위 테스트 (pytest)
    - HWPX 업로드 성공 시 DB 레코드 + 파일 생성 확인
    - 100MB 초과 파일 거부 테스트
    - 비-HWPX 확장자 거부 테스트
    - 태그 없는 템플릿 업로드 시 경고 메시지 + 빈 배열 저장
    - 템플릿 삭제 시 DB + 물리 파일 동시 제거
    - CASCADE 삭제: 프로필 삭제 시 템플릿도 삭제
    - _Requirements: 1.3, 1.5, 1.6, 3.6, 8.2, 9.3_

  - [ ]* 10.3 서버 통합 테스트 (FastAPI TestClient)
    - 전체 업로드 플로우: 파일 전송 → 검증 → 태그 탐지 → DB 저장 → 201 응답
    - 프로필별 목록 필터링 테스트
    - 버전 재업로드 플로우 (동일 파일명 2회 업로드 → version=2)
    - 태그 수정 후 조회 일관성 테스트
    - _Requirements: 1.3, 5.1~5.3, 4.4, 6.1_

  - [ ]* 10.4 프론트엔드 테스트 (Vitest + React Testing Library)
    - TemplateTab 렌더링 + 빈 상태 표시 테스트
    - TemplateList 항목 표시 테스트
    - TemplateUploadButton .hwpx 필터 동작 테스트
    - TagEditor 추가/삭제 인터랙션 테스트
    - TemplatePreview 트리 구조 렌더링 테스트
    - DeleteTemplateDialog 확인/취소 동작 테스트
    - 에러 메시지 표시 테스트
    - _Requirements: 1.1, 4.1, 6.5, 7.4, 8.1, 8.3~8.5_

- [ ] 11. Final Checkpoint - 전체 기능 검증
  - 서버-클라이언트 전체 연동 확인
  - HWPX 업로드 → 유효성 검증 → 태그 탐지 → 목록/상세 → 태그 편집 → 버전 재업로드 → 삭제 전체 플로우
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 서버(Python FastAPI)와 클라이언트(TypeScript/React)는 기존 settings-profile과 동일한 레이어 패턴을 따름
- HWPX 파싱은 Python `zipfile` + `lxml` 라이브러리 사용
- Property 테스트는 Python Hypothesis 라이브러리 사용
- 프론트엔드 테스트는 Vitest + React Testing Library 사용
- 파일 업로드는 multipart/form-data, 100MB 크기 제한 적용
- detected_tags는 JSON TEXT 컬럼으로 저장, 파싱 실패 시 빈 배열 폴백
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from design document

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "6.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.1"] },
    { "id": 3, "tasks": ["3.2", "6.2"] },
    { "id": 4, "tasks": ["3.3", "3.4", "3.5", "3.6", "4.1"] },
    { "id": 5, "tasks": ["4.2", "4.3", "7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 7, "tasks": ["8.1"] },
    { "id": 8, "tasks": ["10.1", "10.2", "10.3", "10.4"] }
  ]
}
```
