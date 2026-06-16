//! mDNS Discovery 클라이언트 모듈
//!
//! 동일 네트워크 내 `_cm-report-server._tcp.local.` 서비스를 검색하여
//! 서버의 IP, 포트, Server-ID를 추출한다.

use mdns_sd::{ServiceDaemon, ServiceEvent};
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// mDNS 서비스 타입 상수
const SERVICE_TYPE: &str = "_cm-report-server._tcp.local.";

/// mDNS 탐색 기본 타임아웃 (초)
const DISCOVERY_TIMEOUT_SECS: u64 = 5;

/// 발견된 서버 정보
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveredServer {
    /// 서버 IP 주소
    pub ip: String,
    /// 서버 포트
    pub port: u16,
    /// 서버 고유 식별자 (UUID v4)
    #[serde(rename = "serverId")]
    pub server_id: String,
    /// 서버 버전 (선택)
    pub version: Option<String>,
}

/// mDNS를 통해 네트워크 내 CM Report 서버를 탐색한다.
///
/// `_cm-report-server._tcp.local.` 서비스를 브라우즈하여
/// 발견된 서버의 IP, 포트, Server-ID, 버전 정보를 추출한다.
///
/// # Arguments
/// * `timeout_secs` - 탐색 타임아웃 (초). None이면 기본값 5초 사용.
///
/// # Returns
/// 발견된 서버 목록
pub fn discover_servers_sync(timeout_secs: Option<u64>) -> Result<Vec<DiscoveredServer>, String> {
    let timeout = Duration::from_secs(timeout_secs.unwrap_or(DISCOVERY_TIMEOUT_SECS));

    // mDNS 데몬 생성
    let mdns = ServiceDaemon::new().map_err(|e| format!("mDNS 데몬 생성 실패: {}", e))?;

    // 서비스 브라우즈 시작
    let receiver = mdns
        .browse(SERVICE_TYPE)
        .map_err(|e| format!("mDNS 브라우즈 시작 실패: {}", e))?;

    let mut servers: Vec<DiscoveredServer> = Vec::new();
    let start = std::time::Instant::now();

    // 타임아웃까지 서비스 이벤트 수신
    loop {
        if start.elapsed() >= timeout {
            break;
        }

        let remaining = timeout.saturating_sub(start.elapsed());

        match receiver.recv_timeout(remaining) {
            Ok(event) => {
                if let ServiceEvent::ServiceResolved(info) = event {
                    // TXT 레코드에서 Server-ID 추출
                    let server_id = info
                        .get_property_val_str("server-id")
                        .unwrap_or_default()
                        .to_string();

                    // TXT 레코드에서 버전 정보 추출
                    let version = info
                        .get_property_val_str("version")
                        .map(|v| v.to_string());

                    // IP 주소 추출 (첫 번째 IPv4 주소 사용)
                    let ip = info
                        .get_addresses()
                        .iter()
                        .find(|addr| addr.is_ipv4())
                        .or_else(|| info.get_addresses().iter().next())
                        .map(|addr| addr.to_string())
                        .unwrap_or_default();

                    let port = info.get_port();

                    // 유효한 서버 정보만 추가 (IP와 Server-ID가 있어야 함)
                    if !ip.is_empty() && !server_id.is_empty() {
                        // 중복 Server-ID 방지
                        if !servers.iter().any(|s| s.server_id == server_id) {
                            servers.push(DiscoveredServer {
                                ip,
                                port,
                                server_id,
                                version,
                            });
                        }
                    }
                }
            }
            Err(flume::RecvTimeoutError::Timeout) => break,
            Err(flume::RecvTimeoutError::Disconnected) => break,
        }
    }

    // 브라우즈 중지 및 데몬 정리
    let _ = mdns.stop_browse(SERVICE_TYPE);
    let _ = mdns.shutdown();

    Ok(servers)
}

/// Tauri 커맨드: 네트워크 내 CM Report 서버 탐색
///
/// React 프론트엔드에서 `invoke('discover_servers')` 으로 호출 가능.
/// mDNS를 통해 `_cm-report-server._tcp.local.` 서비스를 검색하여
/// 발견된 서버 목록을 반환한다.
#[tauri::command]
pub async fn discover_servers(
    timeout_secs: Option<u64>,
) -> Result<Vec<DiscoveredServer>, String> {
    // mDNS 탐색은 블로킹 I/O이므로 별도 스레드에서 실행
    let result = tokio::task::spawn_blocking(move || discover_servers_sync(timeout_secs))
        .await
        .map_err(|e| format!("mDNS 탐색 태스크 실패: {}", e))?;

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_discovered_server_serialization() {
        let server = DiscoveredServer {
            ip: "192.168.1.100".to_string(),
            port: 8741,
            server_id: "550e8400-e29b-41d4-a716-446655440000".to_string(),
            version: Some("1.0.0".to_string()),
        };

        let json = serde_json::to_string(&server).unwrap();
        assert!(json.contains("192.168.1.100"));
        assert!(json.contains("8741"));
        assert!(json.contains("serverId")); // camelCase로 직렬화
        assert!(json.contains("550e8400-e29b-41d4-a716-446655440000"));
        assert!(json.contains("1.0.0"));
    }

    #[test]
    fn test_discovered_server_deserialization() {
        let json = r#"{
            "ip": "10.0.0.5",
            "port": 9000,
            "serverId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "version": null
        }"#;

        let server: DiscoveredServer = serde_json::from_str(json).unwrap();
        assert_eq!(server.ip, "10.0.0.5");
        assert_eq!(server.port, 9000);
        assert_eq!(server.server_id, "a1b2c3d4-e5f6-7890-abcd-ef1234567890");
        assert!(server.version.is_none());
    }
}
