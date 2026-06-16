# CM 월간보고서 자동취합 앱 — 전체 개발 플랜

## 현재 상태

| 완료된 기능 | 진행 상태 |
|------------|-----------|
| 환경설정 프로필 관리 (Spec 01) | ✅ 완료 |
| 서버-클라이언트 아키텍처 | ✅ 완료 |
| 서버 인증 (Server-ID) | ✅ 완료 |
| mDNS 서버 발견 | ✅ 완료 |
| 설치 파일 빌드 시스템 | ✅ 완료 |

---

## 전체 기능 맵 (PRD 기준)

### Part A. 환경설정 (7개 서브 기능)

| # | 기능 | Spec ID | 상태 | 우선순위 |
|---|------|---------|------|----------|
| A1 | 프로필 관리 | settings-profile | ✅ 완료 | - |
| A2 | 월간보고서 HWPX 양식 등록 | template-registration | 미개발 | P1 |
| A3 | 취합 문서 샘플 등록 | document-sample | 미개발 | P1 |
| A4 | 작업폴더 설정 | folder-config | 미개발 | P1 |
| A5 | 대장/사진대지 설정 | ledger-photo-config | 미개발 | P2 |
| A6 | 템플릿 위치 매핑 | template-mapping | 미개발 | P2 |
| A7 | 저장위치/파일명 규칙 | output-config | 미개발 | P2 |
| A8 | LLM 서버 설정 | llm-config | 미개발 | P2 |

### Part B. 자동취합 (6개 서브 기능)

| # | 기능 | Spec ID | 상태 | 우선순위 |
|---|------|---------|------|----------|
| B1 | 기본정보 입력 | collection-input | 미개발 | P1 |
| B2 | 파일 검색 및 날짜 필터링 | file-scanner | 미개발 | P1 |
| B3 | 작업폴더 생성 및 파일 복사 | file-copy | 미개발 | P1 |
| B4 | 자동 분류 | document-classification | 미개발 | P1 |
| B5 | 문서별 데이터 추출 | data-extraction | 미개발 | P1 |
| B6 | AI 요약 (로컬 LLM) | ai-summary | 미개발 | P2 |

### Part C. 검토·수정

| # | 기능 | Spec ID | 상태 | 우선순위 |
|---|------|---------|------|----------|
| C1 | 검토 화면 (전체) | review-screen | 미개발 | P2 |

### Part D. HWPX 월간보고서 생성

| # | 기능 | Spec ID | 상태 | 우선순위 |
|---|------|---------|------|----------|
| D1 | HWPX 생성 엔진 | hwpx-renderer | 미개발 | P1 |
| D2 | 사진대지 생성 | photo-board | 미개발 | P2 |
| D3 | 결과 파일 생성 | report-output | 미개발 | P2 |

### Part E. 이력·로그

| # | 기능 | Spec ID | 상태 | 우선순위 |
|---|------|---------|------|----------|
| E1 | 작업 이력 및 로그 | history-logs | 미개발 | P3 |

---

## MVP 개발 로드맵 (권장 순서)

### Phase 1: 환경설정 완성 (2~3주)

```
Spec 02: template-registration      — HWPX 양식 등록 + 태그 분석
Spec 03: document-sample             — 문서 유형별 샘플 등록
Spec 04: folder-config               — 작업폴더 루트 경로 설정
Spec 05: output-config               — 저장 위치 및 파일명 규칙
```

### Phase 2: 파일 스캔·복사·분류 (3~4주)

```
Spec 06: file-scanner                — 재귀 검색 + 날짜 필터링
Spec 07: file-copy                   — 작업폴더 생성 + 파일 복사 + 충돌 처리
Spec 08: document-classification     — 키워드/유사도 기반 자동 분류
```

### Phase 3: 데이터 추출·대장 생성 (3~4주)

```
Spec 09: data-extraction             — 공문/회의록/공정/안전/검측/기성 데이터 추출
Spec 10: ledger-generation           — 문서 유형별 대장 자동 생성
```

### Phase 4: HWPX 생성 (2~3주)

```
Spec 11: hwpx-renderer               — 태그 치환 + 표 삽입 + 이미지 삽입
Spec 12: photo-board                  — 사진대지 레이아웃 생성
```

### Phase 5: AI 요약·검토 (2~3주)

```
Spec 13: ai-summary                   — 로컬 LLM 연동 + Summary JSON 생성
Spec 14: review-screen                — 사용자 검토·수정 화면
```

### Phase 6: 통합·패키징 (1~2주)

```
Spec 15: report-output                — 최종 결과 파일 생성 + 검증 리포트
Spec 16: history-logs                  — 작업 이력 + 오류 로그
Spec 17: packaging                     — 설치 파일 최종 빌드
```

---

## 각 Spec 상세 내용 요약

### Spec 02: template-registration (월간보고서 HWPX 양식 등록)

**핵심 기능:**
- HWPX 파일 업로드 (서버에 저장)
- HWPX 내부 XML에서 태그 자동 탐색 (PROJECT_NAME, TFA_LIST 등)
- 탐색된 태그 목록 표시
- 사용자가 태그 추가/수정 가능
- 템플릿 버전 관리
- 템플릿 미리보기 (구조 표시)

**기술 요구:**
- Python: zipfile + lxml으로 HWPX 내부 section XML 파싱
- 서버 API: POST /api/v1/templates, GET /api/v1/templates
- 클라이언트: 파일 선택 대화상자 + 태그 목록 편집 UI

---

### Spec 03: document-sample (취합 문서 샘플 등록)

**핵심 기능:**
- 15개 문서 유형별 샘플 파일 등록
- 대표 키워드 / 제외 키워드 설정
- 지원 확장자 설정
- 유사도 기준값 설정
- 대장 생성 여부 / Appendix 삽입 여부 설정

**기술 요구:**
- DB: document_type_config, document_sample 테이블
- 서버 API: CRUD for document types and samples
- 클라이언트: 문서 유형 목록 + 설정 폼

---

### Spec 04: folder-config (작업폴더 설정)

**핵심 기능:**
- 작업폴더 루트 경로 지정 (로컬 폴더 선택)
- 보고월별 하위 폴더 구조 자동 생성 규칙 설정
- 권한 확인 및 오류 표시

---

### Spec 06: file-scanner (파일 검색)

**핵심 기능:**
- 지정 루트 경로 하위 전체 파일 재귀 검색
- 확장자 필터링 (hwpx, docx, xlsx, pdf, jpg, png 등)
- 날짜 필터링 (파일명 날짜 패턴 인식, 파일 수정일, EXIF)
- 검색 결과 목록 표시 (파일수, 총 크기, 유형별 통계)

---

### Spec 08: document-classification (자동 분류)

**핵심 기능:**
- 폴더명 키워드 매칭
- 파일명 키워드 매칭
- 본문 텍스트 추출 후 키워드 매칭
- 분류 신뢰도 산출
- 낮은 신뢰도 → UNKNOWN_미분류
- 사용자 수동 재분류 지원

---

### Spec 09: data-extraction (데이터 추출)

**핵심 기능:**
- HWPX/DOCX에서 공문번호, 일자, 수신처, 제목 추출
- XLSX에서 공정률, 기성금액 추출
- PDF에서 텍스트 추출 (pdfplumber)
- 사진 EXIF에서 촬영일자 추출
- 추출 결과를 JSON 구조로 정리

---

### Spec 11: hwpx-renderer (HWPX 생성 엔진)

**핵심 기능:**
- 템플릿 HWPX 복사
- ZIP 해제 → section XML 로드
- 텍스트 태그 치환 (PROJECT_NAME, WRITE_YYMM 등)
- 표 태그 위치에 대장 데이터 삽입
- 사진대지 태그 위치에 이미지 삽입
- BinData 디렉토리에 이미지 추가
- manifest 갱신 → ZIP 재압축 → HWPX 저장

---

## 기술 스택 (현재 확정)

| 영역 | 기술 |
|------|------|
| 서버 | Python 3.11+, FastAPI, SQLAlchemy, SQLite, uvicorn |
| 클라이언트 | Tauri v2, React 18, TypeScript, Zustand |
| 문서 처리 | zipfile + lxml (HWPX), python-docx (DOCX), openpyxl (XLSX), pdfplumber (PDF) |
| 이미지 | Pillow, piexif |
| LLM | Ollama / LM Studio / OpenAI-compatible local API |
| 테스트 | pytest + Hypothesis (서버), Vitest + RTL (클라이언트) |
| 설치 | PyInstaller + Tauri NSIS + Inno Setup |

---

## 다음 단계 추천

즉시 시작할 수 있는 다음 Spec:

1. **Spec 02: template-registration** — HWPX 양식 등록은 모든 후속 기능의 기반
2. **Spec 03: document-sample** — 자동 분류 기준이 되는 핵심 설정
3. **Spec 04: folder-config** — 파일 복사/생성의 기본 경로

이 3개가 완료되면 자동취합 파이프라인(Phase 2~4) 진행이 가능합니다.
