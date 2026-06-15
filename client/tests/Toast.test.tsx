import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { Toast } from '@/components/Toast';

describe('Toast component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render message when visible', () => {
    render(<Toast message="프로필이 생성되었습니다." type="success" visible={true} onClose={() => {}} />);

    expect(screen.getByText('프로필이 생성되었습니다.')).toBeInTheDocument();
  });

  it('should not render when not visible', () => {
    render(<Toast message="보이지 않는 메시지" type="success" visible={false} onClose={() => {}} />);

    expect(screen.queryByText('보이지 않는 메시지')).not.toBeInTheDocument();
  });

  it('should apply success CSS class for success type', () => {
    render(<Toast message="성공" type="success" visible={true} onClose={() => {}} />);

    const toast = screen.getByTestId('toast');
    expect(toast).toHaveClass('toast--success');
  });

  it('should apply error CSS class for error type', () => {
    render(<Toast message="실패" type="error" visible={true} onClose={() => {}} />);

    const toast = screen.getByTestId('toast');
    expect(toast).toHaveClass('toast--error');
  });

  it('should have role=alert for accessibility', () => {
    render(<Toast message="알림" type="success" visible={true} onClose={() => {}} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('should auto-dismiss success toast after 3 seconds', () => {
    const onClose = vi.fn();
    render(<Toast message="성공" type="success" visible={true} onClose={onClose} />);

    expect(onClose).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should auto-dismiss error toast after 5 seconds', () => {
    const onClose = vi.fn();
    render(<Toast message="에러" type="error" visible={true} onClose={onClose} />);

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(onClose).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<Toast message="닫기 테스트" type="success" visible={true} onClose={onClose} />);

    const closeButton = screen.getByLabelText('알림 닫기');
    closeButton.click();

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
