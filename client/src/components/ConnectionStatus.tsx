import React from "react";
import { useConnectionStore, ConnectionStatus as ConnectionStatusType } from "@/stores/connectionStore";

interface StatusConfig {
  color: string;
  text: string;
}

const STATUS_MAP: Record<ConnectionStatusType, StatusConfig> = {
  connected: { color: "#22c55e", text: "서버 연결됨" },
  connecting: { color: "#eab308", text: "연결 중..." },
  disconnected: { color: "#ef4444", text: "서버 연결 끊김" },
};

/**
 * 서버 연결 상태를 아이콘(색상 점) + 텍스트로 표시하는 컴포넌트.
 * disconnected 상태일 때 쓰기 작업 버튼 비활성화를 위한 disabled prop을 외부에 제공할 수 있다.
 */
export const ConnectionStatus: React.FC = () => {
  const status = useConnectionStore((state) => state.status);
  const { color, text } = STATUS_MAP[status];

  return (
    <div
      className="connection-status"
      style={{ display: "flex", alignItems: "center", gap: "6px" }}
      aria-label={`서버 연결 상태: ${text}`}
    >
      <span
        style={{
          display: "inline-block",
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          backgroundColor: color,
        }}
        aria-hidden="true"
      />
      <span style={{ fontSize: "13px", color: "#374151" }}>{text}</span>
    </div>
  );
};

/**
 * 서버 연결이 끊어졌는지 확인하는 유틸리티 훅.
 * 쓰기 작업 버튼 비활성화 등에 활용.
 */
export const useIsDisconnected = (): boolean => {
  return useConnectionStore((state) => state.status) === "disconnected";
};
