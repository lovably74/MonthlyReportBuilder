import { useToastStore } from '../stores/toastStore';
import { Toast } from './Toast';

/**
 * 토스트 컨테이너
 * 전역 토스트 목록을 렌더링하며, 화면 우측 상단에 위치한다.
 */
export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" data-testid="toast-container">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          visible={true}
          onClose={() => dismiss(toast.id)}
        />
      ))}
    </div>
  );
}

export default ToastContainer;
