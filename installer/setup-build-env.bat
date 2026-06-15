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

set TOOLS_DIR=%~dp0tools
set DOWNLOAD_DIR=%TOOLS_DIR%\downloads

echo.
echo ============================================================================
echo  CM 월간보고서 자동취합 앱 - 빌드 환경 자동 구성
echo ============================================================================
echo.

REM ─── 관리자 권한 확인 ───────────────────────────────────────────────────────
net session >nul 2>&1
if errorlevel 1 (
    echo [오류] 이 스크립트는 관리자 권한으로 실행해야 합니다.
    echo        CMD를 마우스 우클릭 → "관리자 권한으로 실행" 하세요.
    echo.
    pause
    exit /b 1
)

REM ─── 다운로드 폴더 준비 ─────────────────────────────────────────────────────
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

REM ─── winget 확인 ────────────────────────────────────────────────────────────
where winget >nul 2>&1
if errorlevel 1 (
    echo [경고] winget이 설치되어 있지 않습니다.
    echo        Windows 10 1809+ / Windows 11에서는 Microsoft Store에서
    echo        "앱 설치 관리자"를 업데이트하면 winget을 사용할 수 있습니다.
    echo.
    echo        winget 없이 수동 설치를 진행합니다...
    set USE_WINGET=0
) else (
    set USE_WINGET=1
)

set ALL_OK=1

REM ─── 1. Python 확인 및 설치 ─────────────────────────────────────────────────
echo [1/4] Python 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo       Python이 설치되어 있지 않습니다. 설치합니다...
    
    if "!USE_WINGET!"=="1" (
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    ) else (
        echo       Python 다운로드 중...
        set PYTHON_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe
        powershell -Command "Invoke-WebRequest -Uri '!PYTHON_URL!' -OutFile '%DOWNLOAD_DIR%\python-installer.exe'" 2>nul
        if exist "%DOWNLOAD_DIR%\python-installer.exe" (
            echo       Python 설치 중 (자동 모드)...
            "%DOWNLOAD_DIR%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
        ) else (
            echo       [오류] Python 다운로드 실패. 수동 설치하세요: https://python.org
            set ALL_OK=0
        )
    )
    
    REM PATH 새로고침
    call :refresh_path
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo       [경고] Python 설치 후 PATH 인식 안됨. 터미널 재시작 필요할 수 있습니다.
        set ALL_OK=0
    ) else (
        echo       Python 설치 완료!
    )
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo       Python %%v 확인됨.
)
echo.

REM ─── 2. Node.js 확인 및 설치 ────────────────────────────────────────────────
echo [2/4] Node.js 확인 중...
where node >nul 2>&1
if errorlevel 1 (
    echo       Node.js가 설치되어 있지 않습니다. 설치합니다...
    
    if "!USE_WINGET!"=="1" (
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    ) else (
        echo       Node.js 다운로드 중...
        set NODE_URL=https://nodejs.org/dist/v20.15.0/node-v20.15.0-x64.msi
        powershell -Command "Invoke-WebRequest -Uri '!NODE_URL!' -OutFile '%DOWNLOAD_DIR%\node-installer.msi'" 2>nul
        if exist "%DOWNLOAD_DIR%\node-installer.msi" (
            echo       Node.js 설치 중 (자동 모드)...
            msiexec /i "%DOWNLOAD_DIR%\node-installer.msi" /quiet /norestart
        ) else (
            echo       [오류] Node.js 다운로드 실패. 수동 설치하세요: https://nodejs.org
            set ALL_OK=0
        )
    )
    
    call :refresh_path
    
    where node >nul 2>&1
    if errorlevel 1 (
        echo       [경고] Node.js 설치 후 PATH 인식 안됨. 터미널 재시작 필요할 수 있습니다.
        set ALL_OK=0
    ) else (
        echo       Node.js 설치 완료!
    )
) else (
    for /f "tokens=1" %%v in ('node --version 2^>^&1') do echo       Node.js %%v 확인됨.
)
echo.

REM ─── 3. Rust 확인 및 설치 ───────────────────────────────────────────────────
echo [3/4] Rust 확인 중...
where rustc >nul 2>&1
if errorlevel 1 (
    echo       Rust가 설치되어 있지 않습니다. 설치합니다...
    
    if "!USE_WINGET!"=="1" (
        winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements --silent
    ) else (
        echo       rustup-init 다운로드 중...
        set RUSTUP_URL=https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe
        powershell -Command "Invoke-WebRequest -Uri '!RUSTUP_URL!' -OutFile '%DOWNLOAD_DIR%\rustup-init.exe'" 2>nul
        if exist "%DOWNLOAD_DIR%\rustup-init.exe" (
            echo       Rust 설치 중 (자동 모드)...
            "%DOWNLOAD_DIR%\rustup-init.exe" -y --default-toolchain stable 2>nul
        ) else (
            echo       [오류] Rust 다운로드 실패. 수동 설치하세요: https://rustup.rs
            set ALL_OK=0
        )
    )
    
    call :refresh_path
    
    where rustc >nul 2>&1
    if errorlevel 1 (
        echo       [경고] Rust 설치 후 PATH 인식 안됨. 터미널 재시작 필요할 수 있습니다.
        set ALL_OK=0
    ) else (
        echo       Rust 설치 완료!
    )
) else (
    for /f "tokens=2" %%v in ('rustc --version 2^>^&1') do echo       Rust %%v 확인됨.
)
echo.

REM ─── 4. Inno Setup 확인 및 설치 ─────────────────────────────────────────────
echo [4/4] Inno Setup 확인 중...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo       Inno Setup 6이 설치되어 있지 않습니다. 설치합니다...
    
    if "!USE_WINGET!"=="1" (
        winget install JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements --silent
    ) else (
        echo       Inno Setup 다운로드 중...
        set INNO_URL=https://jrsoftware.org/download.php/is.exe
        powershell -Command "Invoke-WebRequest -Uri '!INNO_URL!' -OutFile '%DOWNLOAD_DIR%\innosetup-installer.exe'" 2>nul
        if exist "%DOWNLOAD_DIR%\innosetup-installer.exe" (
            echo       Inno Setup 설치 중 (자동 모드)...
            "%DOWNLOAD_DIR%\innosetup-installer.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
        ) else (
            echo       [오류] Inno Setup 다운로드 실패. 수동 설치하세요: https://jrsoftware.org/isdl.php
            set ALL_OK=0
        )
    )
    
    if exist %ISCC% (
        echo       Inno Setup 설치 완료!
    ) else (
        echo       [경고] Inno Setup 설치 확인 안됨. 기본 경로를 확인하세요.
        set ALL_OK=0
    )
) else (
    echo       Inno Setup 6 확인됨.
)
echo.

REM ─── 추가: Visual Studio Build Tools 확인 (Rust/Tauri 빌드에 필요) ──────────
echo [추가] Visual Studio Build Tools 확인 중...
where cl >nul 2>&1
if errorlevel 1 (
    REM cl.exe가 PATH에 없어도 설치되어 있을 수 있음
    if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" (
        echo       VS Build Tools 2022 확인됨.
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" (
        echo       VS 2022 Community 확인됨.
    ) else (
        echo       [경고] Visual Studio Build Tools가 필요합니다 (Rust/Tauri 빌드용).
        echo.
        
        if "!USE_WINGET!"=="1" (
            echo       VS Build Tools 설치를 시작합니다...
            winget install Microsoft.VisualStudio.2022.BuildTools --accept-source-agreements --accept-package-agreements --silent --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
        ) else (
            echo       수동 설치가 필요합니다:
            echo       https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo       설치 시 "C++ 빌드 도구" 워크로드를 선택하세요.
            set ALL_OK=0
        )
    )
) else (
    echo       C++ 컴파일러 확인됨.
)
echo.

REM ─── 결과 요약 ──────────────────────────────────────────────────────────────
echo ============================================================================
if "!ALL_OK!"=="1" (
    echo  모든 빌드 도구가 준비되었습니다!
    echo.
    echo  다음 명령으로 설치 파일을 빌드하세요:
    echo    cd %~dp0
    echo    build.bat
) else (
    echo  일부 도구 설치에 문제가 있습니다.
    echo  위의 [경고] 메시지를 확인하고, 터미널을 재시작한 후 다시 실행하세요.
    echo.
    echo  터미널 재시작 후에도 문제가 있으면 해당 도구를 수동 설치하세요:
    echo    Python:     https://python.org/downloads/
    echo    Node.js:    https://nodejs.org/
    echo    Rust:       https://rustup.rs/
    echo    Inno Setup: https://jrsoftware.org/isdl.php
    echo    VS Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
)
echo ============================================================================
echo.

REM ─── 다운로드 파일 정리 ─────────────────────────────────────────────────────
if exist "%DOWNLOAD_DIR%" (
    echo  다운로드된 설치 파일을 정리합니다...
    rmdir /s /q "%DOWNLOAD_DIR%" 2>nul
)

pause
goto :eof

REM ─── PATH 새로고침 함수 ─────────────────────────────────────────────────────
:refresh_path
REM 레지스트리에서 최신 PATH를 읽어 현재 세션에 적용
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%b"
set "PATH=%SYS_PATH%;%USR_PATH%"

REM Rust cargo 경로 추가
if exist "%USERPROFILE%\.cargo\bin" set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"

goto :eof

endlocal
