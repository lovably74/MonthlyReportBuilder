; ============================================================================
; CM 월간보고서 자동취합 앱 - Inno Setup 스크립트
; ============================================================================
; 이 스크립트는 서버(Python 임베디드)와 클라이언트(Tauri)를 하나의 설치 파일로 패키징합니다.
;
; 빌드 방법:
;   1. build.bat 실행 (서버/클라이언트 빌드 후 이 스크립트 자동 실행)
;   2. 또는 Inno Setup Compiler에서 직접 열어 컴파일
; ============================================================================

#define MyAppName "CM 월간보고서 자동취합"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "CM Report Team"
#define MyAppURL "https://github.com/cm-report"
#define MyAppExeName "CMMonthlyReport.exe"
#define MyServerExeName "cm-report-server.exe"

[Setup]
AppId={{A7B8C9D0-E1F2-3456-7890-ABCDEF123456}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\CM Monthly Report
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=output
OutputBaseFilename=CMMonthlyReportSetup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\client\CMMonthlyReport.exe

; 설치 시 방화벽 규칙 추가를 위해 관리자 권한 필요
; Windows 10 이상
MinVersion=10.0

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Types]
Name: "full"; Description: "전체 설치 (서버 + 클라이언트)"
Name: "server"; Description: "서버만 설치"
Name: "client"; Description: "클라이언트만 설치"
Name: "custom"; Description: "사용자 정의 설치"; Flags: iscustom

[Components]
Name: "server"; Description: "CM Report 서버 (데이터베이스 및 API)"; Types: full server
Name: "client"; Description: "CM Report 클라이언트 (데스크톱 UI)"; Types: full client

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 클라이언트 바로가기 생성"; GroupDescription: "추가 아이콘:"; Components: client
Name: "desktopicon_server"; Description: "바탕화면에 서버 시작 바로가기 생성"; GroupDescription: "추가 아이콘:"; Components: server
Name: "autostart_server"; Description: "Windows 시작 시 서버 자동 실행"; GroupDescription: "시작 옵션:"; Components: server
Name: "firewall"; Description: "Windows 방화벽 규칙 자동 추가 (포트 8741, 5353)"; GroupDescription: "네트워크:"; Components: server; Flags: checkedonce

[Files]
; ─── 서버 파일 ────────────────────────────────────────────────────────────────
Source: "dist\server\*"; DestDir: "{app}\server"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: server

; ─── 클라이언트 파일 ──────────────────────────────────────────────────────────
Source: "dist\client\*"; DestDir: "{app}\client"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: client

; ─── 문서 ─────────────────────────────────────────────────────────────────────
Source: "dist\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; 서버 데이터 디렉토리 (DB, Server-ID 저장)
Name: "{app}\server\data"; Components: server; Permissions: users-modify

[Icons]
; 시작 메뉴 바로가기
Name: "{group}\{#MyAppName}"; Filename: "{app}\client\{#MyAppExeName}"; Components: client
Name: "{group}\서버 시작"; Filename: "{app}\server\start-server.bat"; IconFilename: "{sys}\cmd.exe"; Components: server
Name: "{group}\서버 중지"; Filename: "{app}\server\stop-server.bat"; IconFilename: "{sys}\cmd.exe"; Components: server
Name: "{group}\설치 매뉴얼"; Filename: "{app}\docs\installation-guide.md"
Name: "{group}\{#MyAppName} 제거"; Filename: "{uninstallexe}"

; 바탕화면 바로가기
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\client\{#MyAppExeName}"; Tasks: desktopicon; Components: client
Name: "{commondesktop}\CM Report 서버 시작"; Filename: "{app}\server\start-server.bat"; Tasks: desktopicon_server; Components: server

[Run]
; 설치 후 실행 옵션
Filename: "{app}\client\{#MyAppExeName}"; Description: "CM 월간보고서 자동취합 실행"; Flags: nowait postinstall skipifsilent; Components: client
Filename: "{app}\server\start-server.bat"; Description: "서버 시작 (로그 창 표시)"; Flags: nowait postinstall skipifsilent; Components: server

[UninstallRun]
; 제거 시 서버 프로세스 종료
Filename: "taskkill"; Parameters: "/f /im cm-report-server.exe"; Flags: runhidden; Components: server

[UninstallDelete]
; 제거 시 데이터 파일 삭제 (사용자 선택)
Type: filesandordirs; Name: "{app}\server\data"

[Code]
// ─── 방화벽 규칙 추가 ────────────────────────────────────────────────────────
procedure AddFirewallRules();
var
  ResultCode: Integer;
begin
  // TCP 8741 (HTTP API)
  Exec('netsh', 'advfirewall firewall add rule name="CM Report Server (TCP 8741)" dir=in action=allow protocol=TCP localport=8741', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // UDP 5353 (mDNS)
  Exec('netsh', 'advfirewall firewall add rule name="CM Report mDNS (UDP 5353)" dir=in action=allow protocol=UDP localport=5353', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ─── 방화벽 규칙 제거 ────────────────────────────────────────────────────────
procedure RemoveFirewallRules();
var
  ResultCode: Integer;
begin
  Exec('netsh', 'advfirewall firewall delete rule name="CM Report Server (TCP 8741)"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('netsh', 'advfirewall firewall delete rule name="CM Report mDNS (UDP 5353)"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ─── 서버 자동 시작 등록 ─────────────────────────────────────────────────────
procedure RegisterAutoStart();
var
  ResultCode: Integer;
begin
  Exec('schtasks', '/create /tn "CM Report Server AutoStart" /tr "' + ExpandConstant('{app}') + '\server\start-server.bat" /sc onlogon /rl highest /f', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ─── 서버 자동 시작 해제 ─────────────────────────────────────────────────────
procedure UnregisterAutoStart();
var
  ResultCode: Integer;
begin
  Exec('schtasks', '/delete /tn "CM Report Server AutoStart" /f', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// ─── 설치 완료 시 후처리 ─────────────────────────────────────────────────────
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 방화벽 규칙 추가
    if IsTaskSelected('firewall') then
      AddFirewallRules();
    
    // 서버 자동 시작 등록
    if IsTaskSelected('autostart_server') then
      RegisterAutoStart();
  end;
end;

// ─── 제거 시 후처리 ──────────────────────────────────────────────────────────
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RemoveFirewallRules();
    UnregisterAutoStart();
  end;
end;

// ─── 기존 서버 중복 실행 확인 ────────────────────────────────────────────────
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // 기존 서버 프로세스가 실행 중이면 종료 안내
  Exec('tasklist', '/fi "imagename eq cm-report-server.exe" /fo csv /nh', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
