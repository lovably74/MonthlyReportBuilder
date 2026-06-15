import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EmptyProfileState } from './EmptyProfileState';

describe('EmptyProfileState', () => {
  it('안내 메시지를 표시한다', () => {
    render(<EmptyProfileState />);

    expect(screen.getByText('등록된 프로필이 없습니다.')).toBeInTheDocument();
  });

  it('"새 프로필 생성" 버튼을 표시한다', () => {
    render(<EmptyProfileState />);

    expect(screen.getByRole('button', { name: '새 프로필 생성' })).toBeInTheDocument();
  });

  it('버튼 클릭 시 onCreate를 호출한다', () => {
    const onCreate = vi.fn();
    render(<EmptyProfileState onCreate={onCreate} />);

    fireEvent.click(screen.getByRole('button', { name: '새 프로필 생성' }));
    expect(onCreate).toHaveBeenCalledTimes(1);
  });
});
