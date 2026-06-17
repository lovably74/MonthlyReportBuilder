# Implementation Plan: 파일 검색 (file-scanner)

## Overview

서버에서 지정된 루트 경로 하위 파일을 재귀 탐색하고, 날짜/확장자 필터를 적용하여 취합 대상 파일 목록을 생성하는 기능을 구현한다. 검색 결과는 임시 JSON으로 저장되어 file-copy에서 참조된다.

## Tasks

- [ ] 1. 핵심 모듈 구현
  - [ ] 1.1 FileWalker 구현
    - `app/services/file_walker.py`에 재귀 파일 탐색 로직
    - 심볼릭 링크 무시, 순환 참조 감지, 접근 불가 폴더 스킵
  - [ ] 1.2 DateExtractor 구현
    - `app/services/date_extractor.py`에 날짜 추출 로직
    - 파일명 패턴(YYYYMMDD, YYYY-MM-DD, YYMMDD), EXIF, mtime 순 우선
  - [ ] 1.3 ExtensionFilter 구현
    - 대소문자 무관 확장자 비교

- [ ] 2. Service 및 API 구현
  - [ ] 2.1 ScanService 구현
    - start_scan, get_status, get_result
    - 결과를 JSON 파일로 임시 저장
  - [ ] 2.2 Scanner API Router
    - POST /api/v1/jobs/{job_id}/scan
    - GET /api/v1/jobs/{job_id}/scan/status
    - GET /api/v1/jobs/{job_id}/scan/result

- [ ] 3. 클라이언트 구현
  - [ ] 3.1 ScanPanel 컴포넌트
    - DateRangeFilter, ExtensionFilter, ScanProgress
  - [ ] 3.2 ScanResultSummary 컴포넌트
    - 총 파일 수, 크기, 확장자별 통계 표시
  - [ ] 3.3 API Client 및 Store

- [ ] 4. 테스트
  - [ ] 4.1 Property Tests: 확장자 필터 정확성, 날짜 필터 범위, 재귀 완전성
  - [ ] 4.2 Unit Tests: DateExtractor 패턴 인식 (다양한 파일명)
  - [ ] 4.3 Integration Tests: 실제 폴더 구조 스캔 플로우

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

- 스캔 결과는 {DATA_DIR}/scan_results/{job_id}.json에 임시 저장
- 대용량 폴더(10만+ 파일) 처리를 위해 비동기 제너레이터 사용
- 클라이언트는 폴링으로 진행 상태 확인 (SSE 대안 검토 가능)
