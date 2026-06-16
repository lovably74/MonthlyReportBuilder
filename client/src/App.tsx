import { useEffect } from 'react';
import { SettingsPage } from './pages/SettingsPage';
import { useConnectionStore } from './stores/connectionStore';

/** 기본 서버 URL (동일 PC 또는 localhost) */
const DEFAULT_SERVER_URL = 'http://localhost:8741';

function App() {
  const { setServerInfo, startHealthCheck } = useConnectionStore();

  useEffect(() => {
    // 앱 시작 시 서버 연결 초기화
    async function initConnection() {
      // mDNS discovery 시도 (Tauri 환경에서만)
      let discovered = false;
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const servers = await invoke<Array<{ ip: string; port: number; serverId: string }>>('discover_servers', { timeoutSecs: 3 });
        if (servers && servers.length > 0) {
          const server = servers[0];
          setServerInfo(`http://${server.ip}:${server.port}`, server.serverId);
          discovered = true;
        }
      } catch {
        // Tauri IPC 실패 (브라우저 환경이거나 mDNS 실패) — 무시
      }

      // mDNS 실패 시 localhost로 fallback
      if (!discovered) {
        // localhost에서 Server-ID를 가져오기 시도
        try {
          const response = await fetch(`${DEFAULT_SERVER_URL}/health`, { signal: AbortSignal.timeout(3000) });
          if (response.ok) {
            // Server-ID는 첫 API 호출 시 헤더에서 확인 — 임시로 빈값 설정
            setServerInfo(DEFAULT_SERVER_URL, 'local');
          }
        } catch {
          // localhost도 응답 없음 — disconnected 상태로 유지
          setServerInfo(DEFAULT_SERVER_URL, 'local');
        }
      }

      // Health check 주기 시작
      startHealthCheck();
    }

    initConnection();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <SettingsPage />;
}

export default App;
