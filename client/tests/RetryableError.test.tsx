import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RetryableError } from '@/components/RetryableError';

describe('RetryableError component', () => {
  it('should render error message', () => {
    render(<RetryableError message="목록을 불러올 수 없습니다." onRetry={() => {}} />);

    expect(screen.getByText('목록을 불러올 수 없습니다.')).toBeInTheDocument();
  });

  it('should render retry button with "다시 시도" text', () => {
    render(<RetryableError message="에러" onRetry={() => {}} />);

    expect(screen.getByRole('button', { name: '다시 시도' })).toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<RetryableError message="에러" onRetry={onRetry} />);

    screen.getByRole('button', { name: '다시 시도' }).click();

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('should have role=alert for accessibility', () => {
    render(<RetryableError message="에러" onRetry={() => {}} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
