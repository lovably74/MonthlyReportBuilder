# Design Document: 사진대지 생성 (photo-board)

## Overview

사진대지 생성은 수집된 사진을 설정된 레이아웃(2x1, 2x2, 2x3, 3x3)에 배치하고 캡션을 추가하여 페이지별 이미지를 생성하는 기능이다. 생성된 사진대지는 HWPX 렌더러에서 이미지로 삽입된다.

### 핵심 설계 결정

1. **Pillow 기반 렌더링**: Python Pillow로 A4 크기 캔버스에 사진+캡션을 합성.
2. **300 DPI**: 인쇄 품질을 위해 A4 기준 300 DPI (2480x3508 px).
3. **촬영일시 정렬**: 사진을 EXIF 촬영일시 순으로 정렬 후 배치.
4. **페이지별 독립 이미지**: 각 페이지를 독립 PNG로 생성.

## Architecture

### 생성 파이프라인

```
photo files + EXIF data (from Spec 09) + config (from Spec 05)
  → PhotoBoardService.generate(job_id)
    → sort photos by taken_date
    → for each page (photos_per_page chunks):
      → PhotoBoardRenderer.render_page(photos, config)
        → create A4 canvas
        → place photos in grid
        → add captions
        → save as PNG
    → return page list + metadata
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/photo_board_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/photo-board` | POST | 사진대지 생성 |
| `/api/v1/jobs/{job_id}/photo-board` | GET | 사진대지 결과 조회 |
| `/api/v1/jobs/{job_id}/photo-board/pages/{page_num}` | GET | 페이지별 이미지 |

#### Service Layer

```python
class PhotoBoardService:
    async def generate(self, job_id: int) -> PhotoBoardResult
    async def get_result(self, job_id: int) -> PhotoBoardResult

class PhotoBoardRenderer:
    def render_page(self, photos: list[PhotoData], config: PhotoBoardConfig) -> str
    def create_canvas(self, width: int, height: int) -> Image
    def place_photo(self, canvas: Image, photo: Image, slot: Rect) -> None
    def add_caption(self, canvas: Image, text: str, position: Point) -> None
```

## Data Models

### Pydantic Schemas

```python
class PhotoData(BaseModel):
    file_path: str
    taken_date: str | None
    description: str

class PhotoBoardResult(BaseModel):
    job_id: int
    total_pages: int
    total_photos: int
    page_paths: list[str]  # PNG file paths
```

## Correctness Properties

### Property 1: 사진 배치 완전성
*For any* N장의 사진과 페이지당 K장 배치 시, 생성 페이지 수는 ceil(N/K)이어야 한다.

### Property 2: 캡션 대응
*For any* 사진에 대해, 해당 슬롯에 캡션이 존재해야 한다 (caption_style != 'none'인 경우).

### Property 3: 정렬 보존
*For any* 연속된 페이지에서, 이전 페이지 마지막 사진의 날짜 ≤ 다음 페이지 첫 사진의 날짜여야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| NO_PHOTOS | 400 | 사진 파일 없음 |
| IMAGE_LOAD_ERROR | 500 | 이미지 로드 실패 |
| CONFIG_NOT_FOUND | 400 | 사진대지 설정 없음 |

## Testing Strategy

- **Property Tests**: 배치 완전성, 캡션 대응, 정렬 보존
- **Unit Tests**: render_page 출력 크기, 캡션 생성 로직
- **Integration Tests**: 전체 생성 플로우, 빈 사진 목록 처리
