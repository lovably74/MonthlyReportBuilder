# Implementation Plan: HWPX 생성 엔진 (hwpx-renderer)

## Overview

템플릿 HWPX를 복사하고 내부 XML의 태그를 데이터로 치환, 표/이미지를 삽입한 뒤 ZIP 재압축하여 최종 보고서 HWPX 파일을 생성하는 핵심 엔진을 구현한다.

## Tasks

- [ ] 1. HWPX 조작 기반 모듈
  - [ ] 1.1 HwpxWorkspace 구현
    - `app/services/hwpx/workspace.py`
    - 템플릿 복사 → ZIP 해제 → 작업 디렉토리 관리 → ZIP 재압축
  - [ ] 1.2 SectionXmlLoader 구현
    - Contents/section*.xml 로드 및 lxml 파싱
    - 수정 후 저장

- [ ] 2. 태그 치환 모듈
  - [ ] 2.1 TextReplacer 구현
    - `app/services/hwpx/text_replacer.py`
    - XML 텍스트 노드 순회 → 태그 패턴 매칭 → 값 치환
    - XML 특수문자 이스케이프 (<, >, &, ", ')
  - [ ] 2.2 TableInserter 구현
    - `app/services/hwpx/table_inserter.py`
    - 표 태그 위치에 HWPX 표 XML 노드 동적 생성/삽입
  - [ ] 2.3 ImageInserter 구현
    - `app/services/hwpx/image_inserter.py`
    - 이미지 태그 위치에 이미지 참조 삽입
    - BinData/ 디렉토리에 이미지 파일 추가
    - manifest XML 갱신

- [ ] 3. 렌더링 서비스 및 API
  - [ ] 3.1 HwpxRendererService 구현
    - render(job_id): 전체 렌더링 오케스트레이션
    - 입력 데이터 조합 (text_data + ledger_data + photo_data + summary_data)
  - [ ] 3.2 Renderer API Router
    - POST /api/v1/jobs/{job_id}/render
    - GET /api/v1/jobs/{job_id}/render/status
    - GET /api/v1/jobs/{job_id}/render/output

- [ ] 4. 클라이언트 구현
  - [ ] 4.1 렌더링 진행 상태 + 결과 표시 UI
  - [ ] 4.2 API Client

- [ ] 5. 테스트
  - [ ] 5.1 Property Tests: 태그 완전 치환, XML 유효성, ZIP 구조, manifest 일관성
  - [ ] 5.2 Unit Tests: TextReplacer 치환, XML 이스케이프, 표 XML 생성
  - [ ] 5.3 Integration Tests: 샘플 템플릿 기반 전체 렌더링 플로우

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3"] },
    { "id": 2, "tasks": ["3.1", "3.2"] },
    { "id": 3, "tasks": ["4.1", "4.2"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3"] }
  ]
}
```

## Notes

- HWPX = ZIP 파일. 내부 구조: Contents/section0.xml, BinData/, META-INF/manifest.xml
- lxml 사용 시 네임스페이스 처리 주의 (HWPX 전용 네임스페이스)
- 이미지 ID는 "image_{순번}" 형식으로 부여
- 표 XML 구조는 한글 HWPX 스펙 참조 필요
