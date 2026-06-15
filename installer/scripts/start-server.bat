@echo off
REM ============================================================================
REM CM Report Server - 서버 시작 스크립트
REM ============================================================================
title CM Report Server

set SERVER_DIR=%~dp0
cd /d "%SERVER_DIR%"

echo.
echo  CM 월간보고서 자동취합 서버를 시작합니다...
echo  포트: 8741
echo  종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.
echo.
echo ============================================================================
echo.

REM 데이터 디렉토리 확인
if not exist "data" mkdir "data"

REM DB 마이그레이션 실행 (처음 실행 시 테이블 생성)
if not exist "data\cm_report.db" (
    echo  데이터베이스를 초기화합니다...
    cm-report-server.exe --init-db 2>nul
    if errorlevel 1 (
        echo  [참고] 자동 초기화 생략. 서버가 시작 시 자동으로 DB를 생성합니다.
    )
    echo.
)

REM 서버 실행
cm-report-server.exe

if errorlevel 1 (
    echo.
    echo  [오류] 서버가 비정상 종료되었습니다.
    echo  오류 코드: %errorlevel%
    echo.
    pause
)
