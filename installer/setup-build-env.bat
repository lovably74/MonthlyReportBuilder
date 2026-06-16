@echo off
REM ============================================================================
REM CM 월간보고서 자동취합 앱 - 빌드 환경 자동 구성 스크립트
REM ============================================================================
REM
REM 이 스크립트는 설치 파일 빌드에 필요한 모든 도구를 자동으로 확인하고,
REM 없으면 다운로드하여 설치합니다.
REM
REM 설치되는 도구:
REM   - Python 3.12 (winget)
REM   - Node.js 20 LTS (winget)
REM   - Rust (rustup-init.exe)
REM   - Inno Setup 6 (직접 다운로드)
REM
REM 사용법:
REM   관리자 권한으로 실행:
REM   setup-build-env.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion

set "TOOLS_DIR=%~dp0tools"
set "DOWNLOAD_DIR=%TOOLS_DIR%\downloads"

echo.
echo ============================================================================
echo  CM 월간보고서 자동취합 앱 - 빌드 환경 자동 구성
echo ============================================================================
echo.

REM ─── 관리자 권한 확인 ───────────────────────────────────────────────────────
net session >nul 2>&1
if errorlevel 1 (
    echo [오류] 이 스크립트는 관리자 권한으로 실행해야 합니다.
    echo        CMD를 마우스 우클릭 - "관리자 권한으로 실행" 하세요.
    echo.
    pause
    exit /b 1
)

REM ─── 다운로드 폴더 준비 ─────────────────────────────────────────────────────
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

REM ─── winget 확인 ────────────────────────────────────────────────────────────
set "USE_WINGET=0"
where winget >nul 2>&1
if not errorlevel 1 set "USE_WINGET=1"

if "%USE_WINGET%"=="0" (
    echo [참고] winget이 없습니다. 직접 다운로드 방식으로 설치합니다.
    echo.
)

set "ALL_OK=1"

REM ─── 1. Python 확인 및 설치 ─────────────────────────────────────────────────
echo [1/4] Python 확인 중...
where python >nul 2>&1
if errorlevel 1 (
    echo       Python이 설치되어 있지 않습니다. 설치합니다...
    call :install_python
) else (
    echo       Python 확인됨.
)
echo.

REM ─── 2. Node.js 확인 및 설치 ────────────────────────────────────────────────
echo [2/4] Node.js 확인 중...
where node >nul 2>&1
if errorlevel 1 (
    echo       Node.js가 설치되어 있지 않습니다. 설치합니다...
    call :install_node
) else (
    echo       Node.js 확인됨.
)
echo.

REM ─── 3. Rust 확인 및 설치 ───────────────────────────────────────────────────
echo [3/4] Rust 확인 중...
where rustc >nul 2>&1
if errorlevel 1 (
    echo       Rust가 설치되어 있지 않습니다. 설치합니다...
    call :install_rust
) else (
    echo       Rust 확인됨.
)
echo.

REM ─── 4. Inno Setup 확인 및 설치 ─────────────────────────────────────────────
echo [4/4] Inno Setup 확인 중...
set "ISCC_CHECK=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%ISCC_CHECK%" goto :inno_found
set "ISCC_CHECK=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%ISCC_CHECK%" goto :inno_found
set "ISCC_CHECK=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ISCC_CHECK%" goto :inno_found
set "ISCC_CHECK=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if exist "%ISCC_CHECK%" goto :inno_found

echo       Inno Setup 6이 설치되어 있지 않습니다. 설치합니다...
call :install_innosetup
goto :inno_done

:inno_found
echo       Inno Setup 6 확인됨: %ISCC_CHECK%
:inno_done
echo.

REM ─── 추가: Visual Studio Build Tools 확인 ──────────────────────────────────
echo [추가] C++ Build Tools 확인 중...
set "VS_FOUND=0"
if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" set "VS_FOUND=1"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" set "VS_FOUND=1"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC" set "VS_FOUND=1"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC" set "VS_FOUND=1"
where cl >nul 2>&1
if not errorlevel 1 set "VS_FOUND=1"
where link >nul 2>&1
if not errorlevel 1 set "VS_FOUND=1"

if "%VS_FOUND%"=="0" (
    echo       [경고] Visual Studio Build Tools가 필요합니다.
    echo       Rust/Tauri 빌드에 C++ 컴파일러가 필요합니다.
    if "%USE_WINGET%"=="1" (
        echo       winget으로 설치합니다...
        winget install Microsoft.VisualStudio.2022.BuildTools --accept-source-agreements --accept-package-agreements --silent --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    ) else (
        echo       수동 설치: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        set "ALL_OK=0"
    )
) else (
    echo       VS Build Tools 확인됨.
)
echo.

REM ─── 결과 요약 ──────────────────────────────────────────────────────────────
echo ============================================================================
if "%ALL_OK%"=="1" (
    echo  모든 빌드 도구가 준비되었습니다!
    echo.
    echo  다음 명령으로 설치 파일을 빌드하세요:
    echo    cd %~dp0
    echo    build.bat
) else (
    echo  일부 도구 설치에 문제가 있습니다.
    echo  터미널을 재시작한 후 다시 실행하세요.
    echo.
    echo  수동 설치 링크:
    echo    Python:     https://python.org/downloads/
    echo    Node.js:    https://nodejs.org/
    echo    Rust:       https://rustup.rs/
    echo    Inno Setup: https://jrsoftware.org/isdl.php
    echo    VS Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
)
echo ============================================================================
echo.

REM ─── 다운로드 파일 정리 ─────────────────────────────────────────────────────
if exist "%DOWNLOAD_DIR%" rmdir /s /q "%DOWNLOAD_DIR%" 2>nul

pause
goto :eof

REM ============================================================================
REM 설치 서브루틴
REM ============================================================================

:install_python
if "%USE_WINGET%"=="1" (
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    if errorlevel 1 (
        echo       [경고] winget 설치 실패. 직접 다운로드합니다...
        goto :install_python_direct
    )
    call :refresh_path
    goto :eof
)
:install_python_direct
echo       Python 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%DOWNLOAD_DIR%\python-installer.exe'"
if exist "%DOWNLOAD_DIR%\python-installer.exe" (
    echo       Python 설치 중...
    "%DOWNLOAD_DIR%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    call :refresh_path
) else (
    echo       [오류] 다운로드 실패. 수동 설치: https://python.org
    set "ALL_OK=0"
)
goto :eof

:install_node
if "%USE_WINGET%"=="1" (
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    if errorlevel 1 (
        echo       [경고] winget 설치 실패. 직접 다운로드합니다...
        goto :install_node_direct
    )
    call :refresh_path
    goto :eof
)
:install_node_direct
echo       Node.js 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.15.0/node-v20.15.0-x64.msi' -OutFile '%DOWNLOAD_DIR%\node-installer.msi'"
if exist "%DOWNLOAD_DIR%\node-installer.msi" (
    echo       Node.js 설치 중...
    msiexec /i "%DOWNLOAD_DIR%\node-installer.msi" /quiet /norestart
    call :refresh_path
) else (
    echo       [오류] 다운로드 실패. 수동 설치: https://nodejs.org
    set "ALL_OK=0"
)
goto :eof

:install_rust
if "%USE_WINGET%"=="1" (
    winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements --silent
    if errorlevel 1 (
        echo       [경고] winget 설치 실패. 직접 다운로드합니다...
        goto :install_rust_direct
    )
    call :refresh_path
    goto :eof
)
:install_rust_direct
echo       rustup-init 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri 'https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe' -OutFile '%DOWNLOAD_DIR%\rustup-init.exe'"
if exist "%DOWNLOAD_DIR%\rustup-init.exe" (
    echo       Rust 설치 중...
    "%DOWNLOAD_DIR%\rustup-init.exe" -y --default-toolchain stable
    call :refresh_path
) else (
    echo       [오류] 다운로드 실패. 수동 설치: https://rustup.rs
    set "ALL_OK=0"
)
goto :eof

:install_innosetup
if "%USE_WINGET%"=="1" (
    winget install JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements --silent
    if errorlevel 1 (
        echo       [경고] winget 설치 실패. 직접 다운로드합니다...
        goto :install_innosetup_direct
    )
    goto :eof
)
:install_innosetup_direct
echo       Inno Setup 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile '%DOWNLOAD_DIR%\innosetup-installer.exe'"
if exist "%DOWNLOAD_DIR%\innosetup-installer.exe" (
    echo       Inno Setup 설치 중...
    "%DOWNLOAD_DIR%\innosetup-installer.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
) else (
    echo       [오류] 다운로드 실패. 수동 설치: https://jrsoftware.org/isdl.php
    set "ALL_OK=0"
)
goto :eof

:refresh_path
REM 레지스트리에서 최신 PATH를 다시 읽어 현재 세션에 반영
for /f "tokens=2,*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2,*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%b"
set "PATH=%SYS_PATH%;%USR_PATH%"
if exist "%USERPROFILE%\.cargo\bin" set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"
goto :eof
