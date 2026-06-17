# Implementation Plan: 최종 결과 파일 생성 (report-output)

## Overview

렌더링된 HWPX 보고서, Excel 대장, 검증 리포트를 설정된 경로에 저장하고 검증 결과를 생성하는 기능을 구현한다. folder_config의 파일명 규칙을 적용한다.

## Tasks

- [ ] 1. 데이터 모델 및 핵심 모듈
  - [ ] 1.1 report_generation 테이블 생성
    - `app/models/report_generation.py`에 ORM 모델 정의
    - FK: job_id → collection_job.id (CASCADE)
  - [ ] 1.2 ExcelExporter 구현
    - `app/services/excel_exporter.py`
    - openpyxl로 문서 유형별 시트 생성
    - 헤더 스타일(굵게, 배경색), 열 너비 설정
  - [ ] 1.3 VerificationReporter 구현
    - `app/services/verification_reporter.py`
    - 태그 치환, 표 삽입, 이미지 삽입, 요약문 검증
    - 결과를 정상/경고/오류로 분류

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 ReportOutputService 구현
    - generate_output: 파일명 규칙 적용 → 파일 저장 → 검증
    - 버전 충돌 방지 (_v{N} 접미사)
  - [ ] 2.2 Report Output API Router
    - POST /api/v1/jobs/{job_id}/output
    - GET /api/v1/jobs/{job_id}/output
    - GET /api/v1/jobs/{job_id}/output/verify

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 결과 생성 진행 + 완료 요약 UI
  - [ ] 3.2 검증 리포트 표시 (정상/경고/오류 항목)
  - [ ] 3.3 API Client

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 산출물 완전성, 파일명 규칙, 검증 정확성
  - [ ] 4.2 Unit Tests: ExcelExporter 시트 생성, VerificationReporter 로직
  - [ ] 4.3 Integration Tests: 전체 출력 플로우

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3"] }
  ]
}
```

## Notes

- 3종 산출물: HWPX 보고서, Excel 대장(.xlsx), 검증 리포트(.txt)
- 파일명 규칙 변수 치환: {PROJECT}, {YYYY}, {MM}, {YYYYMM}, {ROUND}, {DATE}
- 검증 리포트는 사람이 읽을 수 있는 텍스트 형식
