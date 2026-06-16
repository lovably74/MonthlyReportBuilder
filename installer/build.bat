@echo off
REM ============================================================================
REM CM 월간보고서 자동취합 앱 - 통합 설치 파일 빌드 스크립트
REM ============================================================================
REM
REM 사전 요구사항:
REM   1. Python 3.11+
REM   2. Node.js 18+
REM   3. Rust toolchain
REM   4. Inno Setup 6
REM
REM 사용법:
REM   cd h:\projects\MonthlyReportBuilder\installer
REM   build.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0.."
set "INSTALLER_DIR=%~dp0"
set "OUTPUT_DIR=%INSTALLER_DIR%output"
set "DIST_DIR=%INSTALLER_DIR%dist"
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

REM Inno Setup 경로 자동 탐색 (여러 가능한 위치 확인)
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

REM Rust cargo 경로가 PATH에 없을 수 있으므로 명시적으로 추가
if exist "%USERPROFILE%\.cargo\bin" set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"

echo.
echo ============================================================================
echo  CM 월간보고서 자동취합 앱 - 설치 파일 빌드
echo ============================================================================
echo.

REM ─── 빌드 도구 확인 ─────────────────────────────────────────────────────────
echo [사전 확인] 빌드 도구를 점검합니다...
set "MISSING_TOOLS=0"

where python >nul 2>&1
if errorlevel 1 (
    echo   [X] Python 미설치
    set "MISSING_TOOLS=1"
) else (
    echo   [O] Python OK
)

where node >nul 2>&1
if errorlevel 1 (
    echo   [X] Node.js 미설치
    set "MISSING_TOOLS=1"
) else (
    echo   [O] Node.js OK
)

where rustc >nul 2>&1
if errorlevel 1 (
    echo   [X] Rust 미설치
    set "MISSING_TOOLS=1"
) else (
    echo   [O] Rust OK
)

if not exist "%ISCC_PATH%" (
    echo   [X] Inno Setup 미설치
    set "MISSING_TOOLS=1"
) else (
    echo   [O] Inno Setup OK
)

if "!MISSING_TOOLS!"=="1" (
    echo.
    echo   [!] 일부 빌드 도구가 누락되었습니다.
    echo       자동으로 설치하시겠습니까?
    echo.
    choice /c YN /m "       빌드 도구 자동 설치 실행 Y/N"
    if errorlevel 2 goto :error_missing_tools
    echo.
    echo       빌드 도구 설치를 시작합니다...
    call "%INSTALLER_DIR%setup-build-env.bat"
    echo.
    echo       설치 완료. 빌드를 계속합니다...
    echo.
)
echo.

REM ─── Step 1: 이전 빌드 정리 ─────────────────────────────────────────────────
echo [1/5] 이전 빌드 파일 정리 중...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\server"
mkdir "%DIST_DIR%\client"
mkdir "%OUTPUT_DIR%"
echo       완료.
echo.

REM ─── Step 2: 서버 빌드 (PyInstaller) ────────────────────────────────────────
echo [2/5] 서버 빌드 중 (PyInstaller)...
cd /d "%PROJECT_ROOT%\server"

if not exist ".venv" (
    echo       가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

pip install -e . --quiet 2>nul
pip install pyinstaller --quiet 2>nul

pyinstaller --noconfirm --onedir --name "cm-report-server" --paths "." --add-data "alembic;alembic" --add-data "alembic.ini;." --add-data "app;app" --hidden-import "aiosqlite" --hidden-import "sqlalchemy.dialects.sqlite" --hidden-import "uvicorn.logging" --hidden-import "uvicorn.loops.auto" --hidden-import "uvicorn.loops.asyncio" --hidden-import "uvicorn.protocols.http.auto" --hidden-import "uvicorn.protocols.http.h11_impl" --hidden-import "uvicorn.protocols.websockets.auto" --hidden-import "uvicorn.lifespan.on" --hidden-import "uvicorn.lifespan.off" --hidden-import "app" --hidden-import "app.main" --hidden-import "app.core" --hidden-import "app.core.database" --hidden-import "app.core.server_identity" --hidden-import "app.core.mdns_advertiser" --hidden-import "app.core.auth" --hidden-import "app.core.error_handlers" --hidden-import "app.core.exceptions" --hidden-import "app.models" --hidden-import "app.models.settings_profile" --hidden-import "app.schemas" --hidden-import "app.schemas.profile" --hidden-import "app.repositories" --hidden-import "app.repositories.profile_repository" --hidden-import "app.services" --hidden-import "app.services.profile_service" --hidden-import "app.routers" --hidden-import "app.routers.profile_router" --collect-all "zeroconf" --collect-all "uvicorn" --collect-all "fastapi" --collect-all "pydantic" app\main.py

if errorlevel 1 (
    echo [오류] 서버 빌드 실패!
    call deactivate
    goto :error
)

xcopy /e /i /q "dist\cm-report-server" "%DIST_DIR%\server" >nul
call deactivate
echo       서버 빌드 완료.
echo.

REM ─── Step 3: 클라이언트 빌드 (Tauri) ────────────────────────────────────────
echo [3/5] 클라이언트 빌드 중 (Tauri)...
cd /d "%PROJECT_ROOT%\client"

call npm install --silent 2>nul
call npx tauri build --no-bundle

if errorlevel 1 (
    echo [오류] 클라이언트 빌드 실패!
    goto :error
)

REM Tauri 빌드 결과 복사
if exist "src-tauri\target\release\cm-monthly-report.exe" (
    copy "src-tauri\target\release\cm-monthly-report.exe" "%DIST_DIR%\client\CMMonthlyReport.exe" >nul
)
if exist "src-tauri\target\release\bundle\nsis" (
    for %%f in (src-tauri\target\release\bundle\nsis\*.exe) do (
        copy "%%f" "%DIST_DIR%\client\" >nul
    )
)

echo       클라이언트 빌드 완료.
echo.

REM ─── Step 4: 추가 파일 복사 ─────────────────────────────────────────────────
echo [4/5] 추가 파일 복사 중...

copy "%INSTALLER_DIR%scripts\start-server.bat" "%DIST_DIR%\server\" >nul
copy "%INSTALLER_DIR%scripts\stop-server.bat" "%DIST_DIR%\server\" >nul

mkdir "%DIST_DIR%\docs" 2>nul
copy "%PROJECT_ROOT%\docs\installation-guide.md" "%DIST_DIR%\docs\" >nul

echo       완료.
echo.

REM ─── Step 5: Inno Setup으로 설치 파일 생성 ──────────────────────────────────
echo [5/5] 설치 파일 생성 중 (Inno Setup)...

if not exist "%ISCC_PATH%" (
    echo [오류] Inno Setup을 찾을 수 없습니다.
    echo       https://jrsoftware.org/isdl.php 에서 다운로드하세요.
    goto :error
)

"%ISCC_PATH%" "%INSTALLER_DIR%setup.iss"

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

:error_missing_tools
echo       빌드를 중단합니다. 수동 설치 후 다시 실행하세요.
echo.

:error
echo.
echo ============================================================================
echo  빌드 중 오류가 발생했습니다. 위의 오류 메시지를 확인하세요.
echo ============================================================================
pause
exit /b 1

:end
endlocal
