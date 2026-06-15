# 설치 파일 빌드 가이드

## 빌드 결과물

빌드 완료 시 `installer/output/CMMonthlyReportSetup.exe` 설치 파일이 생성됩니다.

## 사전 요구사항

| 도구 | 버전 | 다운로드 |
|------|------|----------|
| Python | 3.11 이상 | https://python.org/downloads/ |
| Node.js | 18 이상 | https://nodejs.org/ |
| Rust | stable | https://rustup.rs/ |
| Inno Setup | 6.x | https://jrsoftware.org/isdl.php |

모든 도구가 시스템 PATH에 등록되어 있어야 합니다.

## 빌드 방법

```cmd
cd h:\projects\MonthlyReportBuilder\installer
build.bat
```

## 빌드 단계

1. **서버 빌드**: PyInstaller로 Python 서버를 단일 디렉토리 exe로 패키징
2. **클라이언트 빌드**: Tauri로 React 앱을 Windows 네이티브 exe로 빌드
3. **파일 수집**: 빌드 결과물과 스크립트를 `dist/` 폴더에 수집
4. **설치 파일 생성**: Inno Setup으로 `CMMonthlyReportSetup.exe` 생성

## 설치 파일 구성

설치 시 사용자가 선택할 수 있는 컴포넌트:

| 컴포넌트 | 설명 |
|----------|------|
| 서버 | FastAPI 서버 + SQLite DB (서버 PC에 설치) |
| 클라이언트 | Tauri 데스크톱 앱 (클라이언트 PC에 설치) |

## 설치 옵션

| 옵션 | 설명 |
|------|------|
| 바탕화면 바로가기 | 클라이언트 바로가기 생성 |
| 서버 자동 실행 | Windows 로그인 시 서버 자동 시작 |
| 방화벽 규칙 | 포트 8741(TCP) + 5353(UDP) 자동 허용 |

## 설치 경로

기본 설치 경로: `C:\Program Files\CM Monthly Report\`

```
CM Monthly Report\
├── server\
│   ├── cm-report-server.exe    # 서버 실행 파일
│   ├── start-server.bat        # 서버 시작 스크립트
│   ├── stop-server.bat         # 서버 중지 스크립트
│   ├── data\                   # DB, Server-ID (런타임 생성)
│   └── ...                     # PyInstaller 번들 파일들
├── client\
│   └── CMMonthlyReport.exe     # 클라이언트 실행 파일
└── docs\
    └── installation-guide.md   # 설치 매뉴얼
```

## 제거 시

- 서버 프로세스 자동 종료
- 방화벽 규칙 자동 삭제
- 자동 시작 스케줄 자동 삭제
- 데이터 파일(`data/`) 삭제

## 수동 빌드 (개별 단계)

### 서버만 빌드

```cmd
cd h:\projects\MonthlyReportBuilder\server
.venv\Scripts\activate
pip install pyinstaller
pyinstaller ..\installer\server.spec
```

### 클라이언트만 빌드

```cmd
cd h:\projects\MonthlyReportBuilder\client
npm install
npm run tauri build
```

### 설치 파일만 생성 (이미 빌드된 dist 폴더가 있을 때)

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" h:\projects\MonthlyReportBuilder\installer\setup.iss
```

## 트러블슈팅

### PyInstaller 빌드 실패

- `pip install pyinstaller --upgrade`로 최신 버전 설치
- 안티바이러스가 exe 생성을 차단하는 경우 예외 등록

### Tauri 빌드 실패

- `rustup update`로 Rust 최신화
- `npm run tauri info`로 환경 확인

### Inno Setup 컴파일 실패

- `dist/` 폴더에 필요한 파일이 모두 있는지 확인
- Inno Setup 6 (5 아님) 설치 확인
