import { useConnectionStore, ConnectionStatus as ConnectionStatusType } from "../stores/connectionStore";

interface StatusConfig {
  color: string;
  text: string;
}

const STATUS_MAP: Record<ConnectionStatusType, StatusConfig> = {
  connected: { color: "#10b981", text: "서버 연결됨" },
  connecting: { color: "#f59e0b", text: "연결 중..." },
  disconnected: { color: "#ef4444", text: "서버 연결 끊김" },
};

/**
 * 서버 연결 상태를 아이콘(색상 점) + 텍스트로 표시하는 컴포넌트.
 */
export const ConnectionStatus: React.FC = () => {
  const status = useConnectionStore((state) => state.status);
  const { color, text } = STATUS_MAP[status];

  return (
    <div
      className="connection-status"
      aria-label={`서버 연결 상태: ${text}`}
    >
      <span
        style={{
          display: "inline-block",
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: color,
          boxShadow: `0 0 6px ${color}`,
        }}
        aria-hidden="true"
      />
      <span style={{ color: status === 'connected' ? color : undefined }}>{text}</span>
    </div>
  );
};

/**
 * 서버 연결이 끊어졌는지 확인하는 유틸리티 훅.
 */
export const useIsDisconnected = (): boolean => {
  return useConnectionStore((state) => state.status) === "disconnected";
};
