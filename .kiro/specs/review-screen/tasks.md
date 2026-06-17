# Implementation Plan: 검토·수정 화면 (review-screen)

## Overview

자동 생성된 대장, 요약문, 사진대지를 사용자가 검토하고 편집하는 통합 화면을 구현한다. 인라인 편집, 자동 저장, 확정/해제 기능을 클라이언트 중심으로 구현한다.

## Tasks

- [ ] 1. 서버 확장
  - [ ] 1.1 Finalize API 추가
    - POST /api/v1/jobs/{job_id}/finalize (상태 → REVIEWED)
    - POST /api/v1/jobs/{job_id}/unfinalize (상태 복원)
  - [ ] 1.2 검토 상태 전제 조건 검증
    - EXTRACTED 이상 상태에서만 확정 허용

- [ ] 2. 클라이언트 구현
  - [ ] 2.1 ReviewPage + 탭 구조
    - 대장/요약문/사진대지 3개 탭
  - [ ] 2.2 LedgerReviewTab + EditableTable
    - 인라인 셀 편집, 행 추가/삭제, 수정 하이라이트
    - '원본 복원' 기능
  - [ ] 2.3 SummaryReviewTab + MarkdownEditor
    - 마크다운 기본 서식, 5초 debounce auto-save
    - 글자 수 카운터, 'AI 재생성' 버튼
  - [ ] 2.4 PhotoBoardReviewTab + PhotoGrid
    - 사진 미리보기, 캡션 편집, 드래그&드롭 순서 변경
    - 사진 교체/삭제 기능
  - [ ] 2.5 FinalizeButton
    - 미검토 항목 경고, 확정/해제 토글

- [ ] 3. 상태 관리
  - [ ] 3.1 ReviewStore (Zustand)
    - 수정 추적, 자동 저장 로직, 확정 상태 관리
  - [ ] 3.2 API Client

- [ ] 4. 테스트
  - [ ] 4.1 Unit Tests: EditableTable 셀 편집, MarkdownEditor 서식
  - [ ] 4.2 Integration Tests: 확정/해제 플로우, auto-save
  - [ ] 4.3 Frontend Tests: 탭 전환, 드래그&드롭

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["4.1", "4.2", "4.3"] }
  ]
}
```

## Notes

- 대장/요약문 데이터 조회는 Spec 10/13의 기존 API 활용
- 클라이언트 중심 기능 (대부분 UI 컴포넌트)
- auto-save는 5초 debounce + 서버 PUT API 호출
