# Implementation Plan: 대장 자동 생성 (ledger-generation)

## Overview

extracted_record 데이터를 ledger_config의 컬럼 정의에 따라 테이블 형식으로 변환하는 기능을 구현한다. JSON 배열 형식으로 출력하여 HWPX 렌더러에 전달한다.

## Tasks

- [ ] 1. 핵심 모듈 구현
  - [ ] 1.1 LedgerBuilder 구현
    - `app/services/ledger_builder.py`
    - 데이터 매핑: data_source → extracted_data 필드
    - 정렬 로직: sort_columns 기반
    - 자동 번호 부여: 첫 컬럼 '번호' 감지
  - [ ] 1.2 셀 형식 변환 유틸
    - format_date (→ YYYY.MM.DD)
    - format_number (→ 천단위 구분자)
    - truncate (100자 말줄임)

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 LedgerGenerationService 구현
    - generate_ledgers: generate_ledger=true 유형별 대장 생성
    - get_ledger: 특정 유형 대장 조회
  - [ ] 2.2 Ledger API Router
    - POST /api/v1/jobs/{job_id}/ledgers
    - GET /api/v1/jobs/{job_id}/ledgers
    - GET /api/v1/jobs/{job_id}/ledgers/{type_code}

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 대장 미리보기 테이블 컴포넌트
  - [ ] 3.2 API Client

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 행 수 일치, 번호 연속성, 정렬 불변식
  - [ ] 4.2 Unit Tests: format_date, format_number, 필드 매핑
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

- 출력 형식: {header: string[], rows: string[][], title: string, type_code: string}
- 빈 필드는 빈 문자열("")로 채움
- 대장 데이터는 메모리에서 생성하여 바로 렌더러에 전달 (별도 DB 저장 불필요)
