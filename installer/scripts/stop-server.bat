@echo off
REM ============================================================================
REM CM Report Server - 서버 중지 스크립트
REM ============================================================================

echo.
echo  CM 월간보고서 서버를 종료합니다...

taskkill /f /im cm-report-server.exe >nul 2>&1

if errorlevel 1 (
    echo  서버 프로세스를 찾을 수 없습니다. (이미 종료됨)
) else (
    echo  서버가 정상적으로 종료되었습니다.
)

echo.
timeout /t 3 >nul
