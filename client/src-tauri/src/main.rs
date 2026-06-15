// CM 월간보고서 자동취합 Tauri 앱 - 메인 엔트리포인트
// Windows 전용: 콘솔 윈도우 비활성화
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    cm_monthly_report_lib::run();
}
