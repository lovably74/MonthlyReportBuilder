# Requirements Document

## Introduction

본 문서는 CM단 월간보고서 AI 자동취합 애플리케이션의 "데이터 추출" 기능에 대한 요구사항을 정의한다.

데이터 추출은 분류된 파일에서 문서 유형별 구조화 데이터를 추출하는 기능이다. 공문에서는 공문번호/일자/수신처/제목, 회의록에서는 일시/참석자/안건, 공정현황에서는 공정률, 사진에서는 EXIF 등을 추출한다.

**연동 관계:**
- **의존**: Spec 08 (document-classification) — 분류된 파일 (classified_type)
- **의존**: 문서 처리 라이브러리 (python-docx, openpyxl, pdfplumber, Pillow)
- **제공**: Spec 10 (ledger-generation)에 추출된 구조화 데이터 전달
- **제공**: Spec 13 (ai-summary)에 추출된 텍스트 데이터 전달
- DB: extracted_record 테이블

## Glossary

- **Extracted_Record**: 파일에서 추출된 구조화 데이터 레코드
- **Extraction_Schema**: 문서 유형별 추출 대상 필드 정의
- **Parser**: 파일 형식별 데이터 추출기 (HwpxParser, DocxParser, XlsxParser, PdfParser, ImageParser)

## Requirements

### Requirement 1: 문서 유형별 데이터 추출

**User Story:** As a CM단 문서 담당자, I want 분류된 문서에서 핵심 데이터가 자동으로 추출되도록, so that 대장 작성에 필요한 정보를 수동으로 입력하지 않아도 된다.

#### Acceptance Criteria

1. WHEN 분류된 파일에 대해 추출이 시작되면, THE System SHALL classified_type에 따라 적절한 Parser를 선택하고 데이터를 추출한다.
2. THE System SHALL 공문 유형에서 공문번호, 발신일자, 수신처, 제목, 내용요약을 추출한다.
3. THE System SHALL 회의록 유형에서 회의일시, 참석자, 안건, 결정사항을 추출한다.
4. THE System SHALL 공정현황에서 공정률(%), 기준일, 실적 데이터를 추출한다.
5. THE System SHALL 사진 파일에서 EXIF(촬영일시, GPS), 파일명 기반 설명을 추출한다.
6. WHEN 추출이 완료되면, THE System SHALL extracted_record 테이블에 JSON 형식으로 저장한다.
7. IF 파일 파싱 중 오류가 발생하면, THEN THE System SHALL 해당 파일을 스킵하고 오류 원인을 로그에 기록한다.

### Requirement 2: 파일 형식별 파서

**User Story:** As a 시스템 관리자, I want 다양한 파일 형식을 처리할 수 있도록, so that HWPX, DOCX, XLSX, PDF, 이미지 등 현장에서 사용하는 모든 문서를 지원한다.

#### Acceptance Criteria

1. THE System SHALL HWPX 파일에서 zipfile+lxml으로 section XML 텍스트를 추출한다.
2. THE System SHALL DOCX 파일에서 python-docx로 단락/표/이미지를 추출한다.
3. THE System SHALL XLSX 파일에서 openpyxl로 시트/셀 데이터를 추출한다.
4. THE System SHALL PDF 파일에서 pdfplumber로 텍스트/표를 추출한다.
5. THE System SHALL 이미지 파일(JPG, PNG)에서 Pillow/piexif로 EXIF 메타데이터를 추출한다.
6. IF 지원하지 않는 파일 형식이면, THEN THE System SHALL 해당 파일을 스킵하고 '미지원 형식' 로그를 기록한다.

### Requirement 3: 추출 결과 관리

**User Story:** As a CM단 문서 담당자, I want 추출 결과를 확인하고 수정할 수 있도록, so that 잘못 추출된 데이터를 보정할 수 있다.

#### Acceptance Criteria

1. WHEN 추출이 완료되면, THE System SHALL 파일별 추출 결과를 JSON 형식으로 조회할 수 있는 API를 제공한다.
2. THE System SHALL 추출된 필드 수, 비어있는 필드 수, 추출 신뢰도를 요약 표시한다.
3. WHEN 사용자가 추출 결과를 수정하면, THE System SHALL 수정된 값을 DB에 반영하고 is_manual_edited=true로 표시한다.
4. THE System SHALL 추출 작업 완료 후 collection_job 상태를 EXTRACTED로 변경한다.
5. IF 전체 파일 중 50% 이상 추출 실패 시, THEN THE System SHALL 경고를 표시하고 설정 점검을 안내한다.
