# Design Document: HWPX 생성 엔진 (hwpx-renderer)

## Overview

HWPX 렌더러는 템플릿 HWPX를 복사하고 내부 XML의 태그를 데이터로 치환, 표/이미지를 삽입한 뒤 ZIP 재압축하여 최종 보고서를 생성하는 핵심 엔진이다.

### 핵심 설계 결정

1. **ZIP 조작**: HWPX는 ZIP 파일이므로 해제→수정→재압축 패턴.
2. **lxml 기반 XML 조작**: section XML을 lxml로 파싱하여 태그를 정밀하게 교체.
3. **이미지 관리**: BinData/ 디렉토리에 이미지 추가, manifest 갱신.
4. **표 생성**: HWPX 표 XML 구조에 맞는 노드를 동적으로 생성.

## Architecture

### 렌더링 파이프라인

```
template HWPX (from Spec 02)
  → HwpxRenderer.render(job_id)
    → copy template to work_dir
    → unzip
    → for each section*.xml:
      → TextReplacer.replace(xml, text_data)
      → TableInserter.insert(xml, ledger_data)
      → ImageInserter.insert(xml, photo_data)
    → update manifest
    → rezip → output HWPX
```

## Components and Interfaces

### Backend Components

#### API Router (`app/routers/renderer_router.py`)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/v1/jobs/{job_id}/render` | POST | 렌더링 시작 |
| `/api/v1/jobs/{job_id}/render/status` | GET | 렌더링 상태 |
| `/api/v1/jobs/{job_id}/render/output` | GET | 결과 파일 경로 |

#### Service Layer

```python
class HwpxRendererService:
    async def render(self, job_id: int) -> RenderResult

class TextReplacer:
    def replace(self, xml_tree: etree.Element, data: dict) -> etree.Element

class TableInserter:
    def insert(self, xml_tree: etree.Element, tag_name: str, table: LedgerTable) -> etree.Element

class ImageInserter:
    def insert(self, xml_tree: etree.Element, tag_name: str, image_path: str) -> etree.Element
    def add_to_bindata(self, zip_path: str, image_path: str) -> str
    def update_manifest(self, manifest_xml: etree.Element, resource_id: str) -> None
```

## Data Models

### Pydantic Schemas

```python
class RenderInput(BaseModel):
    job_id: int
    text_data: dict[str, str]  # tag_name -> value
    ledger_data: dict[str, LedgerTable]  # tag_name -> table
    photo_data: dict[str, str]  # tag_name -> image_path

class RenderResult(BaseModel):
    job_id: int
    output_path: str
    tags_replaced: int
    tables_inserted: int
    images_inserted: int
    warnings: list[str]
```

## Correctness Properties

### Property 1: 태그 완전 치환
*For any* 렌더링 완료 후, section XML에 미치환 태그(사전정의 패턴)가 남아있지 않아야 한다.

### Property 2: XML well-formed 보존
*For any* 모든 수정 작업 후, section XML은 유효한 well-formed XML이어야 한다.

### Property 3: ZIP 구조 보존
*For any* 재압축 후, HWPX 파일은 원본과 동일한 디렉토리 구조를 유지해야 한다.

### Property 4: manifest 일관성
*For any* BinData에 추가된 이미지는 manifest에 등록되어야 하며, manifest의 모든 항목은 실제 파일이 존재해야 한다.

## Error Handling

| 에러 | HTTP 코드 | 설명 |
|------|----------|------|
| TEMPLATE_NOT_FOUND | 404 | 템플릿 파일 없음 |
| INVALID_TEMPLATE | 400 | 손상된 HWPX 템플릿 |
| XML_GENERATION_ERROR | 500 | XML 생성 실패 |
| IMAGE_NOT_FOUND | 400 | 삽입할 이미지 파일 없음 |
| ZIP_ERROR | 500 | ZIP 재압축 실패 |

## Testing Strategy

- **Property Tests**: 태그 완전 치환, XML 유효성, ZIP 구조, manifest 일관성
- **Unit Tests**: TextReplacer 치환 정확성, XML 특수문자 이스케이프
- **Integration Tests**: 전체 렌더링 플로우 (템플릿→결과 HWPX)
- **Frontend Tests**: 렌더링 상태 표시, 결과 다운로드
