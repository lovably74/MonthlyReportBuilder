# Implementation Plan: 작업폴더 설정 (folder-config)

## Overview

작업폴더 루트 경로, 작업폴더 경로, 결과물 저장 경로, 파일명 규칙을 프로필별로 설정하는 기능을 구현한다. 서버에 folder_config 테이블을 추가하고, 클라이언트에 경로 선택 및 규칙 편집 UI를 구현한다.

## Tasks

- [ ] 1. 데이터 모델 및 마이그레이션
  - [ ] 1.1 folder_config 테이블 생성
    - `app/models/folder_config.py`에 ORM 모델 정의
    - Alembic 마이그레이션 작성
    - UNIQUE 제약: profile_id
  - [ ] 1.2 Pydantic 스키마 정의
    - `app/schemas/folder_config.py`에 FolderConfigUpdate, FolderConfigResponse, PathValidationResult 정의

- [ ] 2. Repository 및 Service 구현
  - [ ] 2.1 FolderConfigRepository 구현
    - get_by_profile, upsert 메서드
  - [ ] 2.2 FolderConfigService 구현
    - get_config, upsert_config, validate_paths, preview_filename
    - 경로 정규화, 금지 문자 검증, 변수 치환 로직

- [ ] 3. API Router 구현
  - [ ] 3.1 폴더 설정 API
    - GET /api/v1/folder-config?profile_id=
    - PUT /api/v1/folder-config
    - POST /api/v1/folder-config/validate

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 FolderConfigTab 컴포넌트
    - PathInput (경로 표시 + Tauri 폴더 선택 대화상자 연동)
  - [ ] 4.2 NamingRuleEditor 컴포넌트
    - 변수 버튼({PROJECT}, {YYYY} 등) + 실시간 미리보기
  - [ ] 4.3 PathValidator 컴포넌트
    - 경로별 존재/권한 상태 아이콘 표시
  - [ ] 4.4 API Client 및 Store
    - `api/folderConfigApi.ts`, `stores/folderConfigStore.ts`

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 경로 정규화 라운드트립, 파일명 변수 치환 무결성
  - [ ] 5.2 Unit/Integration Tests: upsert 동작, 경로 검증
  - [ ] 5.3 Frontend Tests: PathInput, NamingRuleEditor 미리보기

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- 프로필당 folder_config는 최대 1개 (UNIQUE profile_id)
- Tauri dialog API로 폴더 선택 후 서버에 경로 문자열 전달
- 파일명 규칙 변수: {PROJECT}, {YYYY}, {MM}, {YYYYMM}, {ROUND}, {DATE}
