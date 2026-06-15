/**
 * mDNS 서버 탐색 API
 *
 * Tauri IPC를 통해 Rust 측 mDNS Discovery 커맨드를 호출하여
 * 동일 네트워크 내 CM Report 서버를 탐색한다.
 */

import { invoke } from '@tauri-apps/api/core';
import type { DiscoveredServer } from '../types/server';

/** 기본 탐색 타임아웃 (초) */
const DEFAULT_TIMEOUT_SECS = 5;

/**
 * 네트워크 내 CM Report 서버를 mDNS로 탐색한다.
 *
 * `_cm-report-server._tcp.local.` 서비스를 브라우즈하여
 * 발견된 서버의 IP, 포트, Server-ID, 버전 정보를 반환한다.
 *
 * @param timeoutSecs - 탐색 타임아웃 (초). 기본값 5초.
 * @returns 발견된 서버 목록
 * @throws Tauri IPC 호출 실패 시 에러 문자열
 *
 * @example
 * ```ts
 * const servers = await discoverServers();
 * if (servers.length > 0) {
 *   console.log(`서버 발견: ${servers[0].ip}:${servers[0].port}`);
 * }
 * ```
 */
export async function discoverServers(
  timeoutSecs: number = DEFAULT_TIMEOUT_SECS,
): Promise<DiscoveredServer[]> {
  return invoke<DiscoveredServer[]>('discover_servers', {
    timeoutSecs,
  });
}

/**
 * 발견된 서버 정보로 기본 URL을 생성한다.
 *
 * @param server - 발견된 서버 정보
 * @returns HTTP 기본 URL (예: "http://192.168.1.100:8741")
 */
export function buildServerBaseUrl(server: DiscoveredServer): string {
  return `http://${server.ip}:${server.port}`;
}
