/**
 * mDNS를 통해 발견된 서버 정보 타입 정의
 *
 * Tauri IPC 커맨드 `discover_servers`의 응답 타입으로 사용된다.
 * Rust 측 DiscoveredServer 구조체와 1:1 대응한다.
 */

/** mDNS로 발견된 CM Report 서버 정보 */
export interface DiscoveredServer {
  /** 서버 IP 주소 (IPv4) */
  ip: string;
  /** 서버 포트 번호 */
  port: number;
  /** 서버 고유 식별자 (UUID v4) - IP 변경과 무관하게 서버를 식별 */
  serverId: string;
  /** 서버 버전 정보 (선택) */
  version?: string;
}

/** 서버 연결 상태 */
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

/** 서버 연결 정보 (연결 수립 후 사용) */
export interface ServerConnection {
  /** 발견된 서버 정보 */
  server: DiscoveredServer;
  /** 서버 기본 URL (예: http://192.168.1.100:8741) */
  baseUrl: string;
  /** 현재 연결 상태 */
  status: ConnectionStatus;
}
