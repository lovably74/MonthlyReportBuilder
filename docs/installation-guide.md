# CM 월간보고서 자동취합 앱 — 설치 및 사용 매뉴얼

## 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [시스템 구조](#2-시스템-구조)
3. [서버 설치](#3-서버-설치)
4. [클라이언트 설치](#4-클라이언트-설치)
5. [실행 방법](#5-실행-방법)
6. [환경설정 프로필 사용법](#6-환경설정-프로필-사용법)
7. [API 참조](#7-api-참조)
8. [문제 해결](#8-문제-해결)
9. [개발 환경 설정](#9-개발-환경-설정)

---

## 1. 시스템 요구사항

### 서버 (Server PC)

| 항목 | 요구사항 |
|------|----------|
| OS | Windows 10/11 (64bit) |
| Python | 3.11 이상 |
| 메모리 | 4GB 이상 권장 |
| 디스크 | 500MB 이상 여유공간 |
| 네트워크 | LAN 연결 (인터넷 불필요) |

### 클라이언트 (Client PC)

| 항목 | 요구사항 |
|------|----------|
| OS | Windows 10/11 (64bit) |
| 메모리 | 2GB 이상 권장 |
| 디스크 | 200MB 이상 여유공간 |
| 네트워크 | 서버와 동일 LAN |

### 네트워크 요구사항

- 서버와 클라이언트가 **동일 네트워크(LAN)**에 연결되어 있어야 합니다.
- 인터넷 연결은 필요하지 않습니다 (완전 오프라인 동작).
- 서버 포트 **8741**이 방화벽에서 허용되어야 합니다.
- mDNS 트래픽 (UDP 5353)이 허용되어야 서버 자동 발견이 동작합니다.

---

## 2. 시스템 구조

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│     Server PC               │         │     Client PC (Tauri App)   │
│                             │         │                             │
│  ┌───────────────────────┐  │  HTTP   │  ┌───────────────────────┐  │
│  │  FastAPI (port 8741)  │◄─┼─────────┼──│  React + TypeScript   │  │
│  └───────────────────────┘  │         │  └───────────────────────┘  │
│  ┌───────────────────────┐  │  mDNS   │  ┌───────────────────────┐  │
│  │  mDNS Advertiser      │◄─┼─────────┼──│  mDNS Discovery       │  │
│  └───────────────────────┘  │         │  └───────────────────────┘  │
│  ┌───────────────────────┐  │         │  ┌───────────────────────┐  │
│  │  SQLite Database      │  │         │  │  Local Cache           │  │
│  └───────────────────────┘  │         │  └───────────────────────┘  │
└─────────────────────────────┘         └─────────────────────────────┘
```

- **서버**: 중앙 데이터베이스(SQLite)와 API를 관리합니다.
- **클라이언트**: Tauri 기반 데스크톱 앱으로, 서버 API를 호출하여 UI를 제공합니다.
- **서버 발견**: mDNS를 사용하여 클라이언트가 자동으로 서버를 찾습니다.
- **오프라인 읽기**: 서버 연결 끊김 시 로컬 캐시로 프로필 목록 조회가 가능합니다.

---

## 3. 서버 설치

### 3.1 Python 설치

Python 3.11 이상이 설치되어 있지 않다면 [python.org](https://www.python.org/downloads/)에서 다운로드합니다.

설치 확인:
```cmd
python --version
```

### 3.2 프로젝트 디렉토리 이동

```cmd
cd h:\projects\MonthlyReportBuilder\server
```

### 3.3 가상환경 생성 및 활성화

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3.4 의존성 설치

```cmd
pip install -e .
```

개발 도구(테스트 프레임워크 등)도 설치하려면:
```cmd
pip install -e ".[dev]"
```

### 3.5 데이터베이스 초기화

```cmd
alembic upgrade head
```

이 명령은 `server/data/cm_report.db` SQLite 파일을 생성하고 테이블을 구성합니다.

### 3.6 방화벽 설정

Windows 방화벽에서 포트 8741 인바운드 규칙을 추가합니다:

```cmd
netsh advfirewall firewall add rule name="CM Report Server" dir=in action=allow protocol=TCP localport=8741
```

mDNS를 위해 UDP 5353도 허용합니다:
```cmd
netsh advfirewall firewall add rule name="CM Report mDNS" dir=in action=allow protocol=UDP localport=5353
```

---

## 4. 클라이언트 설치

### 4.1 사전 요구사항

빌드된 설치 파일(.msi 또는 .exe)을 배포받은 경우, 더블 클릭하여 설치합니다.

### 4.2 개발 빌드 (소스에서 빌드 시)

#### Node.js 설치
Node.js 18 이상 필요. [nodejs.org](https://nodejs.org/) 다운로드.

#### Rust 설치
Rust toolchain 필요. [rustup.rs](https://rustup.rs/) 설치.

#### 빌드 절차

```cmd
cd h:\projects\MonthlyReportBuilder\client

rem 1. Node 의존성 설치
npm install

rem 2. Tauri 앱 빌드
npm run tauri build
```

빌드 결과물은 `client/src-tauri/target/release/bundle/` 하위에 생성됩니다.

---

## 5. 실행 방법

### 5.1 서버 실행

```cmd
cd h:\projects\MonthlyReportBuilder\server
.venv\Scripts\activate
python -m app.main
```

정상 실행 시 출력:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8741
```

서버 상태 확인:
```cmd
curl http://localhost:8741/health
```

응답: `{"status":"ok"}`

### 5.2 클라이언트 실행

설치된 앱을 실행하면 자동으로:
1. mDNS를 통해 동일 네트워크의 서버를 탐색합니다.
2. 서버 발견 시 자동으로 연결합니다.
3. 프로필 관리 화면이 표시됩니다.

### 5.3 서버 자동 시작 (선택)

Windows 서비스로 등록하거나, 시작 프로그램에 추가하여 PC 부팅 시 자동 실행할 수 있습니다:

```cmd
rem 작업 스케줄러에 등록 (예시)
schtasks /create /tn "CM Report Server" /tr "h:\projects\MonthlyReportBuilder\server\.venv\Scripts\python.exe -m app.main" /sc onlogon
```

---

## 6. 환경설정 프로필 사용법

### 6.1 프로필이란?

프로필은 현장별·양식별·발주처별 보고서 생성 기준정보를 담는 설정 단위입니다.
여러 프로필을 만들어 다양한 보고서 시나리오에 대응할 수 있습니다.

### 6.2 프로필 생성

1. 환경설정 화면의 "프로필" 탭에서 **"새 프로필"** 버튼을 클릭합니다.
2. 프로필명(필수, 1~50자)과 설명(선택, 최대 200자)을 입력합니다.
3. **"생성"** 버튼을 클릭합니다.

> 첫 번째 프로필은 자동으로 기본 프로필로 지정됩니다.

### 6.3 프로필 수정

1. 프로필 목록에서 수정할 프로필을 클릭합니다.
2. 이름 또는 설명을 변경합니다.
3. **"저장"** 버튼을 클릭합니다.

### 6.4 프로필 복사

1. 프로필 목록에서 복사할 프로필을 선택합니다.
2. **"복사"** 버튼을 클릭합니다.
3. "원본이름 (복사본)" 형식으로 새 프로필이 생성됩니다.

### 6.5 프로필 삭제

1. 삭제할 프로필을 선택하고 **"삭제"** 버튼을 클릭합니다.
2. 확인 대화상자에서 **"삭제"**를 클릭합니다.

> 마지막 1개의 프로필은 삭제할 수 없습니다.
> 기본 프로필을 삭제하면 가장 최근 수정된 프로필이 자동으로 기본 프로필로 지정됩니다.

### 6.6 기본 프로필 지정

1. 기본으로 사용할 프로필을 선택합니다.
2. **"기본 프로필로 지정"** 기능을 실행합니다.
3. 자동취합 실행 시 해당 프로필이 자동 적용됩니다.

### 6.7 프로필 내보내기

1. 내보낼 프로필을 선택하고 **"내보내기"** 버튼을 클릭합니다.
2. 파일 저장 대화상자에서 저장 위치를 선택합니다.
3. `profile_[프로필명]_[날짜].json` 형식의 파일이 저장됩니다.

### 6.8 프로필 가져오기

1. **"가져오기"** 버튼을 클릭합니다.
2. `.json` 파일을 선택합니다.
3. 이름 충돌 시 새 이름 입력 대화상자가 표시됩니다.

> 파일 크기 제한: 10MB 이하

### 6.9 서버 연결 끊김 시

- 프로필 **목록 조회**는 로컬 캐시를 통해 계속 가능합니다 (읽기 전용).
- **생성, 수정, 삭제, 복사** 등 쓰기 작업은 차단됩니다.
- 화면 상단에 "서버와 연결이 끊어졌습니다. 읽기 전용 모드로 동작합니다." 배너가 표시됩니다.
- 서버 연결이 복구되면 자동으로 최신 데이터를 갱신합니다.

---

## 7. API 참조

서버 API는 `http://<서버IP>:8741` 에서 제공됩니다.

### 인증

모든 API 요청(health 제외)에는 `X-Server-ID` 헤더가 필요합니다.
Server-ID는 서버 최초 실행 시 생성되며, `server/data/server_id.json`에 저장됩니다.

### 엔드포인트 목록

| Method | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 (인증 불필요) |
| GET | `/api/v1/profiles` | 프로필 목록 조회 |
| POST | `/api/v1/profiles` | 프로필 생성 |
| GET | `/api/v1/profiles/{id}` | 프로필 상세 조회 |
| PUT | `/api/v1/profiles/{id}` | 프로필 수정 |
| DELETE | `/api/v1/profiles/{id}` | 프로필 삭제 |
| POST | `/api/v1/profiles/{id}/copy` | 프로필 복사 |
| PUT | `/api/v1/profiles/{id}/default` | 기본 프로필 지정 |
| GET | `/api/v1/profiles/{id}/export` | 프로필 내보내기 |
| POST | `/api/v1/profiles/import` | 프로필 가져오기 |

### 에러 응답 형식

```json
{
  "error_code": "PROFILE_NOT_FOUND",
  "message": "해당 프로필을 찾을 수 없습니다.",
  "detail": "Profile with id=999 not found.",
  "field": null
}
```

### 에러 코드

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| PROFILE_NAME_REQUIRED | 422 | 프로필명 미입력 |
| PROFILE_NAME_TOO_LONG | 422 | 프로필명 50자 초과 |
| PROFILE_DESC_TOO_LONG | 422 | 설명 200자 초과 |
| PROFILE_NAME_DUPLICATE | 409 | 프로필명 중복 |
| PROFILE_NOT_FOUND | 404 | 프로필 미존재 |
| PROFILE_LAST_DELETE | 400 | 마지막 프로필 삭제 시도 |
| IMPORT_INVALID_JSON | 400 | 유효하지 않은 JSON |
| IMPORT_MISSING_FIELD | 400 | 필수 필드 누락 |
| IMPORT_FILE_TOO_LARGE | 400 | 파일 크기 10MB 초과 |

---

## 8. 문제 해결

### 서버가 시작되지 않는 경우

| 증상 | 원인 | 해결방법 |
|------|------|----------|
| `Address already in use` | 포트 8741 이미 사용 중 | 다른 프로세스 종료 또는 포트 변경 |
| `ModuleNotFoundError` | 의존성 미설치 | `pip install -e .` 재실행 |
| `Duplicate server detected` | 네트워크에 다른 서버 존재 | 기존 서버 종료 후 재시작 |

### 클라이언트에서 서버를 찾지 못하는 경우

1. 서버가 실행 중인지 확인합니다 (`curl http://<서버IP>:8741/health`)
2. 클라이언트와 서버가 **동일 네트워크(서브넷)**에 있는지 확인합니다.
3. 방화벽에서 포트 8741(TCP)과 5353(UDP)이 허용되었는지 확인합니다.
4. VPN이나 네트워크 가상화가 mDNS 트래픽을 차단하고 있는지 확인합니다.

### "서버와 연결이 끊어졌습니다" 메시지

- 서버 프로세스가 종료되었거나 네트워크 연결이 불안정합니다.
- 서버를 재시작한 후 5초 이내에 자동으로 재연결됩니다.
- 재연결 시 프로필 목록이 자동으로 갱신됩니다.

### 프로필 이름 중복 오류

- 프로필명은 **대소문자 무관**하게 고유해야 합니다.
- "현장A"와 "현장a"는 동일한 이름으로 간주됩니다.

### 데이터베이스 초기화 (주의: 모든 데이터 삭제)

```cmd
cd h:\projects\MonthlyReportBuilder\server
del data\cm_report.db
alembic upgrade head
```

---

## 9. 개발 환경 설정

### 9.1 서버 개발

```cmd
cd h:\projects\MonthlyReportBuilder\server
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

rem 테스트 실행
python -m pytest tests/ -v

rem 서버 개발 모드 실행 (auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8741 --reload
```

### 9.2 클라이언트 개발

```cmd
cd h:\projects\MonthlyReportBuilder\client
npm install

rem 프론트엔드 개발 서버
npm run dev

rem Tauri 개발 모드 (프론트엔드 + 데스크톱 창)
npm run tauri dev

rem 테스트 실행
npm test

rem 프로덕션 빌드
npm run tauri build
```

### 9.3 프로젝트 구조

```
MonthlyReportBuilder/
├── server/                      # Python FastAPI 서버
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── core/                # 인증, DB, mDNS, 에러 핸들러
│   │   ├── models/              # SQLAlchemy ORM 모델
│   │   ├── schemas/             # Pydantic 스키마
│   │   ├── repositories/        # 데이터 접근 계층
│   │   ├── routers/             # API 라우터
│   │   └── services/            # 비즈니스 로직
│   ├── alembic/                 # DB 마이그레이션
│   ├── data/                    # SQLite DB, Server-ID 파일
│   ├── tests/                   # pytest 테스트
│   └── pyproject.toml           # Python 프로젝트 설정
├── client/                      # Tauri + React 클라이언트
│   ├── src/
│   │   ├── pages/               # 페이지 컴포넌트
│   │   ├── components/          # UI 컴포넌트
│   │   ├── stores/              # Zustand 상태 관리
│   │   ├── api/                 # API 클라이언트
│   │   ├── cache/               # 로컬 캐시
│   │   └── types/               # TypeScript 타입 정의
│   ├── src-tauri/               # Rust (Tauri 코어)
│   │   ├── src/                 # mDNS Discovery 등
│   │   └── Cargo.toml           # Rust 의존성
│   ├── tests/                   # Vitest 테스트
│   └── package.json             # Node.js 의존성
└── docs/                        # 문서
```

### 9.4 주요 기술 스택

| 영역 | 기술 |
|------|------|
| 서버 런타임 | Python 3.11+, FastAPI, uvicorn |
| 서버 DB | SQLite + SQLAlchemy (async) |
| 서버 마이그레이션 | Alembic |
| 서버 발견 | zeroconf (mDNS/DNS-SD) |
| 클라이언트 프레임워크 | Tauri v2 + React 18 + TypeScript |
| 상태 관리 | Zustand |
| 클라이언트 mDNS | mdns-sd (Rust crate) |
| 서버 테스트 | pytest, Hypothesis (PBT) |
| 클라이언트 테스트 | Vitest, React Testing Library |

---

## 부록: 서버 데이터 파일

| 파일 | 위치 | 설명 |
|------|------|------|
| `cm_report.db` | `server/data/` | SQLite 데이터베이스 |
| `server_id.json` | `server/data/` | 서버 고유 식별자 (UUID v4) |

> `server_id.json`을 삭제하면 서버가 새로운 ID를 생성합니다. 이 경우 기존에 연결된 클라이언트는 재인증이 필요합니다.
