@echo off
REM ============================================================================
REM CM 월간보고서 자동취합 앱 - 통합 설치 파일 빌드 스크립트
REM ============================================================================
REM
REM 사전 요구사항:
REM   1. Python 3.11+ (PATH에 등록)
REM   2. Node.js 18+ (PATH에 등록)
REM   3. Rust toolchain (rustup)
REM   4. Inno Setup 6 (기본 경로: C:\Program Files (x86)\Inno Setup 6)
REM
REM 사용법:
REM   cd h:\projects\MonthlyReportBuilder\installer
REM   build.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set INSTALLER_DIR=%~dp0
set OUTPUT_DIR=%INSTALLER_DIR%output
set DIST_DIR=%INSTALLER_DIR%dist

REM Inno Setup 경로 (기본 설치 경로)
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

echo.
echo ============================================================================
echo  CM 월간보고서 자동취합 앱 - 설치 파일 빌드
echo ============================================================================
echo.

REM ─── Step 0-A: 빌드 도구 확인 ───────────────────────────────────────────────
echo [사전 확인] 빌드 도구를 점검합니다...
set MISSING_TOOLS=0

where python >nul 2>&1
if errorlevel 1 (
    echo   [X] Python 미설치
    set MISSING_TOOLS=1
) else (
    echo   [O] Python OK
)

where node >nul 2>&1
if errorlevel 1 (
    echo   [X] Node.js 미설치
    set MISSING_TOOLS=1
) else (
    echo   [O] Node.js OK
)

where rustc >nul 2>&1
if errorlevel 1 (
    echo   [X] Rust 미설치
    set MISSING_TOOLS=1
) else (
    echo   [O] Rust OK
)

if not exist %ISCC% (
    echo   [X] Inno Setup 미설치
    set MISSING_TOOLS=1
) else (
    echo   [O] Inno Setup OK
)

if "%MISSING_TOOLS%"=="1" (
    echo.
    echo   [!] 일부 빌드 도구가 누락되었습니다.
    echo       자동으로 설치하시겠습니까?
    echo.
    choice /c YN /m "       빌드 도구 자동 설치를 실행할까요 (Y/N)"
    if errorlevel 2 (
        echo       빌드를 중단합니다. 수동 설치 후 다시 실행하세요.
        goto :error
    )
    echo.
    echo       빌드 도구 설치를 시작합니다...
    call "%INSTALLER_DIR%setup-build-env.bat"
    echo.
    echo       설치 완료. 빌드를 계속합니다...
    echo.
)
echo.

REM ─── Step 0-B: 이전 빌드 정리 ───────────────────────────────────────────────
echo [1/5] 이전 빌드 파일 정리 중...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\server"
mkdir "%DIST_DIR%\client"
mkdir "%OUTPUT_DIR%"
echo       완료.
echo.

REM ─── Step 1: 서버 빌드 (PyInstaller) ────────────────────────────────────────
echo [2/5] 서버 빌드 중 (PyInstaller)...
cd /d "%PROJECT_ROOT%\server"

REM 가상환경이 없으면 생성
if not exist ".venv" (
    echo       가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM 의존성 및 PyInstaller 설치
pip install -e . --quiet 2>nul
pip install pyinstaller --quiet 2>nul

REM Alembic 마이그레이션 파일 포함하여 PyInstaller 실행
pyinstaller ^
    --noconfirm ^
    --onedir ^
    --name "cm-report-server" ^
    --add-data "alembic;alembic" ^
    --add-data "alembic.ini;." ^
    --hidden-import "aiosqlite" ^
    --hidden-import "sqlalchemy.dialects.sqlite" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --collect-all "zeroconf" ^
    --collect-all "uvicorn" ^
    --collect-all "fastapi" ^
    app\main.py

if errorlevel 1 (
    echo [오류] 서버 빌드 실패!
    goto :error
)

REM 빌드 결과를 dist 폴더로 복사
xcopy /e /i /q "dist\cm-report-server" "%DIST_DIR%\server" >nul

call deactivate
echo       서버 빌드 완료.
echo.

REM ─── Step 2: 클라이언트 빌드 (Tauri) ────────────────────────────────────────
echo [3/5] 클라이언트 빌드 중 (Tauri)...
cd /d "%PROJECT_ROOT%\client"

REM Node 의존성 설치
call npm install --silent 2>nul

REM Tauri 빌드
call npm run tauri build

if errorlevel 1 (
    echo [오류] 클라이언트 빌드 실패!
    goto :error
)

REM Tauri 빌드 결과에서 exe 복사
for /r "src-tauri\target\release" %%f in (*.exe) do (
    if "%%~nxf"=="CM Monthly Report.exe" (
        copy "%%f" "%DIST_DIR%\client\CMMonthlyReport.exe" >nul
    )
)

REM 대체: bundle 폴더에서 msi가 있으면 별도 보관
if exist "src-tauri\target\release\bundle\nsis\*.exe" (
    copy "src-tauri\target\release\bundle\nsis\*.exe" "%DIST_DIR%\client\" >nul
)

echo       클라이언트 빌드 완료.
echo.

REM ─── Step 3: 추가 파일 복사 ─────────────────────────────────────────────────
echo [4/5] 추가 파일 복사 중...

REM 서버 시작 스크립트
copy "%INSTALLER_DIR%\scripts\start-server.bat" "%DIST_DIR%\server\" >nul
copy "%INSTALLER_DIR%\scripts\stop-server.bat" "%DIST_DIR%\server\" >nul

REM 문서
mkdir "%DIST_DIR%\docs" 2>nul
copy "%PROJECT_ROOT%\docs\installation-guide.md" "%DIST_DIR%\docs\" >nul

echo       완료.
echo.

REM ─── Step 4: Inno Setup으로 설치 파일 생성 ──────────────────────────────────
echo [5/5] 설치 파일 생성 중 (Inno Setup)...

if not exist %ISCC% (
    echo [오류] Inno Setup을 찾을 수 없습니다.
    echo       설치 경로: C:\Program Files (x86)\Inno Setup 6
    echo       https://jrsoftware.org/isdl.php 에서 다운로드하세요.
    goto :error
)

%ISCC% "%INSTALLER_DIR%\setup.iss"

if errorlevel 1 (
    echo [오류] 설치 파일 생성 실패!
    goto :error
)

echo       설치 파일 생성 완료.
echo.

REM ─── 완료 ───────────────────────────────────────────────────────────────────
echo ============================================================================
echo  빌드 완료!
echo  설치 파일: %OUTPUT_DIR%\CMMonthlyReportSetup.exe
echo ============================================================================
echo.
goto :end

:error
echo.
echo ============================================================================
echo  빌드 중 오류가 발생했습니다. 위의 오류 메시지를 확인하세요.
echo ============================================================================
exit /b 1

:end
endlocal
