# Implementation Plan: 대장/사진대지 설정 (ledger-photo-config)

## Overview

문서 유형별 대장 컬럼 설정과 사진대지 레이아웃 설정을 프로필별로 관리하는 기능을 구현한다. ledger_config, photo_board_config 테이블을 추가하고, 컬럼 편집기와 레이아웃 미리보기 UI를 구현한다.

## Tasks

- [ ] 1. 데이터 모델 및 마이그레이션
  - [ ] 1.1 ledger_config 테이블 생성
    - `app/models/ledger_config.py`에 ORM 모델 정의
    - 인덱스: (profile_id, type_code) UNIQUE
  - [ ] 1.2 photo_board_config 테이블 생성
    - `app/models/photo_board_config.py`에 ORM 모델 정의
    - UNIQUE: profile_id
  - [ ] 1.3 Pydantic 스키마 정의

- [ ] 2. Repository 및 Service 구현
  - [ ] 2.1 LedgerPhotoConfigRepository 구현
  - [ ] 2.2 LedgerPhotoConfigService 구현
    - 컬럼 수 검증(2~15), 레이아웃 enum 검증
    - generate_ledger=true인 유형별 기본 컬럼 설정 자동 생성

- [ ] 3. API Router 구현
  - [ ] 3.1 대장 설정 및 사진대지 설정 API
    - GET/PUT /api/v1/ledger-configs
    - GET/PUT /api/v1/photo-board-config

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 LedgerConfigTab + ColumnEditor 컴포넌트
    - 컬럼 추가/삭제/정렬(드래그&드롭)
  - [ ] 4.2 PhotoBoardConfigTab + LayoutPreview 컴포넌트
    - 레이아웃 선택 + 미리보기 스케치
  - [ ] 4.3 API Client 및 Store

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 컬럼 라운드트립, 컬럼 수 제한, enum 유효성
  - [ ] 5.2 Unit/Integration Tests: 설정 저장→조회, CASCADE 삭제
  - [ ] 5.3 Frontend Tests: ColumnEditor, LayoutPreview

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- document_type_config.generate_ledger=true인 유형에만 ledger_config 적용
- 컬럼 정의는 JSON 배열로 저장: [{name, width_pct, data_source}]
- 사진대지 레이아웃: 2x1(2장), 2x2(4장), 2x3(6장), 3x3(9장)
