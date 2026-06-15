// CM 월간보고서 자동취합 Tauri 앱 - 라이브러리 엔트리포인트

mod mdns;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![mdns::discover_servers])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
