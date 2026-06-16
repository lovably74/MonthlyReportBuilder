@echo off
REM ============================================================================
REM CM Report Server - 서버 시작 스크립트 (로그 창 포함)
REM ============================================================================
title CM Report Server - 포트 8741

color 0A
set "SERVER_DIR=%~dp0"
cd /d "%SERVER_DIR%"

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║         CM 월간보고서 자동취합 - 서버                       ║
echo  ║                                                            ║
echo  ║  포트: 8741                                                ║
echo  ║  상태: 시작 중...                                          ║
echo  ║                                                            ║
echo  ║  이 창을 닫으면 서버가 종료됩니다.                         ║
echo  ║  Ctrl+C로도 종료할 수 있습니다.                            ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo  [%date% %time%] 서버를 시작합니다...
echo.
echo  ────────────────────── 서버 로그 ──────────────────────────────
echo.

REM _internal 폴더가 있으면 PyInstaller 번들 환경
if exist "%SERVER_DIR%_internal" (
    "%SERVER_DIR%cm-report-server.exe"
) else if exist "%SERVER_DIR%cm-report-server.exe" (
    "%SERVER_DIR%cm-report-server.exe"
) else (
    echo  [오류] cm-report-server.exe를 찾을 수 없습니다.
    echo  설치 경로: %SERVER_DIR%
    echo.
    pause
    exit /b 1
)

echo.
echo  ────────────────────────────────────────────────────────────────
echo.
echo  [%date% %time%] 서버가 종료되었습니다.
echo.

if errorlevel 1 (
    color 0C
    echo  [오류] 서버가 비정상적으로 종료되었습니다.
    echo  오류 코드: %errorlevel%
    echo.
    echo  일반적인 해결 방법:
    echo    1. 포트 8741이 다른 프로그램에 의해 사용 중인지 확인
    echo    2. 방화벽에서 포트 8741 허용 여부 확인
    echo    3. 앱을 재설치하거나 관리자 권한으로 실행
    echo.
)
pause
