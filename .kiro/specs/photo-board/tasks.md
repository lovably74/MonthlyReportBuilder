# Implementation Plan: 사진대지 생성 (photo-board)

## Overview

수집된 사진을 설정된 레이아웃에 배치하고 캡션을 추가하여 페이지별 PNG 이미지를 생성하는 기능을 구현한다. Pillow를 사용하여 A4 300DPI 기준 이미지를 합성한다.

## Tasks

- [ ] 1. 핵심 모듈 구현
  - [ ] 1.1 PhotoBoardRenderer 구현
    - `app/services/photo_board_renderer.py`
    - A4 캔버스 생성 (2480x3508 px at 300 DPI)
    - 그리드 기반 사진 배치 (2x1, 2x2, 2x3, 3x3)
    - 이미지 크롭/리사이즈 (aspect_ratio 적용)
  - [ ] 1.2 CaptionGenerator 구현
    - `app/services/caption_generator.py`
    - 캡션 스타일별 텍스트 생성
    - 50자 초과 말줄임 처리

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 PhotoBoardService 구현
    - generate: 사진 정렬 → 페이지 분할 → 렌더링
    - 결과 PNG 저장 + 메타데이터 JSON
  - [ ] 2.2 PhotoBoard API Router
    - POST /api/v1/jobs/{job_id}/photo-board
    - GET /api/v1/jobs/{job_id}/photo-board
    - GET /api/v1/jobs/{job_id}/photo-board/pages/{page_num}

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 사진대지 미리보기 + 편집 UI
  - [ ] 3.2 API Client

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 배치 완전성, 캡션 대응, 정렬 보존
  - [ ] 4.2 Unit Tests: 렌더러 출력 크기, 캡션 생성, 크롭 로직
  - [ ] 4.3 Integration Tests: 전체 생성 플로우

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "3.2"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] }
  ]
}
```

## Notes

- 출력: {DATA_DIR}/photo_boards/{job_id}/page_{N}.png
- Pillow ImageFont로 캡션 텍스트 렌더링 (한글 폰트 필요)
- 사진 없으면 사진대지 미생성 (태그를 빈 상태로 남김)
