# Implementation Plan: 데이터 추출 (data-extraction)

## Overview

분류된 파일에서 문서 유형별 구조화 데이터를 추출하는 기능을 구현한다. 파일 형식별 파서(HWPX, DOCX, XLSX, PDF, Image)를 전략 패턴으로 구현하고, extracted_record 테이블에 JSON 결과를 저장한다.

## Tasks

- [ ] 1. 데이터 모델 및 파서 인프라
  - [ ] 1.1 extracted_record 테이블 생성
    - `app/models/extracted_record.py`에 ORM 모델 정의
    - FK: job_id, file_id (CASCADE)
  - [ ] 1.2 BaseParser 추상 클래스 및 ParserFactory
    - `app/services/parsers/base_parser.py`
    - `app/services/parsers/parser_factory.py`
  - [ ] 1.3 추출 스키마 정의
    - 문서 유형별 추출 대상 필드 매핑

- [ ] 2. 파서 구현
  - [ ] 2.1 HwpxDocParser (zipfile + lxml)
  - [ ] 2.2 DocxParser (python-docx)
  - [ ] 2.3 XlsxParser (openpyxl)
  - [ ] 2.4 PdfParser (pdfplumber)
  - [ ] 2.5 ImageParser (Pillow + piexif)

- [ ] 3. Service 및 API 구현
  - [ ] 3.1 ExtractionService 구현
    - extract_job, get_records, update_record
    - 개별 실패 스킵, 50% 이상 실패 시 경고
  - [ ] 3.2 Extraction API Router
    - POST /api/v1/jobs/{job_id}/extract
    - GET /api/v1/jobs/{job_id}/records
    - PUT /api/v1/jobs/{job_id}/records/{record_id}

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 추출 진행 상태 + 결과 요약 UI
  - [ ] 4.2 추출 결과 편집 폼
  - [ ] 4.3 API Client 및 Store

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 추출 완전성, 스키마 준수, 수동 편집 보존
  - [ ] 5.2 Unit Tests: 각 Parser별 추출 정확성 (샘플 파일 기반)
  - [ ] 5.3 Integration Tests: 전체 추출 플로우

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "2.5"] },
    { "id": 2, "tasks": ["3.1", "3.2"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- 라이브러리 의존성: python-docx, openpyxl, pdfplumber, Pillow, piexif
- extracted_data는 JSON TEXT 컬럼 (유연한 필드 구조)
- is_manual_edited=true인 레코드는 재추출 시 보호
