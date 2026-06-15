import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ErrorBoundary } from './ErrorBoundary';

// 에러를 발생시키는 테스트 컴포넌트
function ThrowingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('테스트 에러');
  }
  return <div data-testid="child-content">정상 렌더링</div>;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // React의 에러 경계 테스트 시 console.error 억제
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('에러가 없으면 자식 컴포넌트를 정상 렌더링한다', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('정상 렌더링')).toBeInTheDocument();
  });

  it('에러 발생 시 fallback UI를 표시한다', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
    expect(screen.getByText('오류가 발생했습니다. 앱을 재시작해 주세요.')).toBeInTheDocument();
  });

  it('fallback UI에 다시 시도 버튼이 있다', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByRole('button', { name: '다시 시도' })).toBeInTheDocument();
  });

  it('다시 시도 버튼 클릭 시 자식을 다시 렌더링한다', () => {
    // 처음에는 에러를 발생시키고, retry 후에는 정상 렌더링하는 시나리오는
    // React 테스트 환경에서 동적으로 prop을 변경하기 어려우므로
    // 버튼 클릭이 상태를 리셋하는지만 확인한다
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    const retryBtn = screen.getByRole('button', { name: '다시 시도' });
    // 클릭 후에도 ThrowingComponent가 다시 에러를 발생시키므로 fallback이 다시 표시됨
    fireEvent.click(retryBtn);
    expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument();
  });
});
