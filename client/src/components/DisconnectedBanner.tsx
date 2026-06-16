import { useConnectionStore } from "../stores/connectionStore";

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
    <div className="disconnected-banner" role="alert">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0 }}>
        <path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM7.25 4.5h1.5v4h-1.5v-4zm.75 7a.75.75 0 110-1.5.75.75 0 010 1.5z" fill="currentColor"/>
      </svg>
      서버와 연결이 끊어졌습니다. 읽기 전용 모드로 동작합니다.
    </div>
  );
};
