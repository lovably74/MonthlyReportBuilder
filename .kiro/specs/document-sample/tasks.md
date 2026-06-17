# Implementation Plan: 취합 문서 샘플 등록 (document-sample)

## Overview

15개 문서 유형별 샘플 파일과 분류 기준(키워드, 유사도 임계값, 확장자)을 관리하는 기능을 구현한다. 서버에 document_type_config, document_sample 테이블을 추가하고, 클라이언트에 설정 UI를 구현한다.

## Tasks

- [ ] 1. 데이터 모델 및 마이그레이션
  - [ ] 1.1 document_type_config 테이블 생성
    - `app/models/document_type_config.py`에 ORM 모델 정의
    - Alembic 마이그레이션 작성
    - 인덱스: (profile_id, type_code) UNIQUE
  - [ ] 1.2 document_sample 테이블 생성
    - `app/models/document_sample.py`에 ORM 모델 정의
    - FK: type_config_id → document_type_config.id (CASCADE)
  - [ ] 1.3 Pydantic 스키마 정의
    - `app/schemas/document_sample.py`에 요청/응답 모델 정의

- [ ] 2. Repository 및 Service 구현
  - [ ] 2.1 DocumentSampleRepository 구현
    - CRUD 메서드: list_types, get_type, update_type, create_sample, delete_sample
  - [ ] 2.2 DocumentSampleService 구현
    - initialize_types: 15개 기본 유형 자동 생성
    - upload_sample: 파일 저장 + DB 레코드 생성
    - 키워드 파싱/유효성 검증, 임계값 범위 검증
  - [ ] 2.3 15개 기본 문서 유형 시드 데이터 정의
    - 기본 type_code, display_name, include_keywords, supported_extensions

- [ ] 3. API Router 구현
  - [ ] 3.1 문서 유형 CRUD API
    - GET /api/v1/document-types, GET/PUT /{type_id}
  - [ ] 3.2 샘플 파일 업로드/삭제 API
    - POST /api/v1/document-types/{type_id}/samples (multipart, 50MB 제한)
    - DELETE /api/v1/document-types/{type_id}/samples/{sample_id}

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 DocumentSampleTab 컴포넌트
    - 문서 유형 목록 + 상세 설정 패널
  - [ ] 4.2 TypeConfigForm 컴포넌트
    - 키워드 편집, 유사도 슬라이더, 확장자 체크박스
  - [ ] 4.3 SampleFileList 컴포넌트
    - 샘플 파일 목록 + 업로드/삭제 버튼
  - [ ] 4.4 API Client 및 Store
    - `api/documentSampleApi.ts`, `stores/documentSampleStore.ts`

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 키워드 라운드트립, 임계값 범위, 샘플 수 제한
  - [ ] 5.2 Unit/Integration Tests: 기본 유형 초기화, 업로드→조회→삭제
  - [ ] 5.3 Frontend Tests: TypeConfigForm 유효성, SampleFileList 렌더링

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3"] },
    { "id": 2, "tasks": ["3.1", "3.2"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- 프로필 삭제 시 CASCADE로 document_type_config → document_sample 모두 삭제
- 샘플 파일 물리 경로: {DATA_DIR}/samples/{profile_id}/{type_code}/
- 기본 15개 유형은 PRD 기준 (공문, 회의록, 공정현황, 안전점검, 검측기록, 자재반입, 기성내역, 시험성과, 품질시험, 사진대지, 인력현황, 장비현황, 환경관리, NCR, 기타)
