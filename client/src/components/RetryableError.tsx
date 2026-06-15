export interface RetryableErrorProps {
  message: string;
  onRetry: () => void;
}

/**
 * 재시도 가능한 에러 표시 컴포넌트
 * 목록 로드 실패 시 에러 메시지와 재시도 버튼을 제공한다.
 */
export function RetryableError({ message, onRetry }: RetryableErrorProps) {
  return (
    <div className="retryable-error" role="alert" data-testid="retryable-error">
      <p className="retryable-error__message">{message}</p>
      <button
        className="retryable-error__retry-button"
        onClick={onRetry}
        type="button"
      >
        다시 시도
      </button>
    </div>
  );
}

export default RetryableError;
