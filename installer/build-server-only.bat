@echo off
REM ============================================================================
REM CM Report Server - 서버만 빌드 (PyInstaller)
REM ============================================================================
REM 전체 빌드 없이 서버 exe만 빠르게 생성하고 싶을 때 사용합니다.
REM ============================================================================

setlocal
set PROJECT_ROOT=%~dp0..
set SERVER_DIR=%PROJECT_ROOT%\server

echo.
echo  서버 빌드를 시작합니다...
echo.

cd /d "%SERVER_DIR%"

if not exist ".venv" (
    echo  가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -e . --quiet
pip install pyinstaller --quiet

echo  PyInstaller 실행 중...
pyinstaller "%~dp0server.spec" --noconfirm

if errorlevel 1 (
    echo.
    echo  [오류] 서버 빌드 실패!
    call deactivate
    exit /b 1
)

call deactivate

echo.
echo  빌드 완료!
echo  결과물: %SERVER_DIR%\dist\cm-report-server\
echo.
endlocal
