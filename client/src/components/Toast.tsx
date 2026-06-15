import { useEffect } from 'react';

export interface ToastProps {
  message: string;
  type: 'success' | 'error';
  visible: boolean;
  onClose: () => void;
}

/** 자동 소멸 시간(ms): success=3초, error=5초 */
const AUTO_DISMISS_MS: Record<ToastProps['type'], number> = {
  success: 3000,
  error: 5000,
};

/**
 * 토스트 알림 컴포넌트
 * 성공/실패 메시지를 일정 시간 후 자동으로 닫는다.
 */
export function Toast({ message, type, visible, onClose }: ToastProps) {
  useEffect(() => {
    if (!visible) return;

    const timer = setTimeout(onClose, AUTO_DISMISS_MS[type]);
    return () => clearTimeout(timer);
  }, [visible, type, onClose]);

  if (!visible) return null;

  return (
    <div
      className={`toast toast--${type}`}
      role="alert"
      aria-live="assertive"
      data-testid="toast"
    >
      <span className="toast__message">{message}</span>
      <button
        className="toast__close"
        onClick={onClose}
        aria-label="알림 닫기"
        type="button"
      >
        ×
      </button>
    </div>
  );
}

export default Toast;
