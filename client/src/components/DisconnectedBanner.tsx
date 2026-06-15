import React from "react";
import { useConnectionStore } from "@/stores/connectionStore";

/**
 * 서버 연결 끊김 시 상단에 표시되는 경고 배너.
 * role="alert"로 접근성을 보장한다.
 */
export const DisconnectedBanner: React.FC = () => {
  const status = useConnectionStore((state) => state.status);

  if (status !== "disconnected") {
    return null;
  }

  return (
    <div
      role="alert"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        backgroundColor: "#fef2f2",
        borderBottom: "1px solid #fca5a5",
        padding: "8px 16px",
        textAlign: "center",
        color: "#991b1b",
        fontSize: "14px",
      }}
    >
      서버와 연결이 끊어졌습니다. 읽기 전용 모드로 동작합니다.
    </div>
  );
};
