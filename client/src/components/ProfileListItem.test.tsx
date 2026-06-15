import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ProfileListItem, truncateDescription } from './ProfileListItem';
import type { Profile } from '../types/profile';

function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return {
    id: 1,
    name: '테스트 프로필',
    description: '간단한 설명',
    is_default: false,
    created_at: '2024-01-15T09:00:00Z',
    updated_at: '2024-06-20T14:30:00Z',
    ...overrides,
  };
}

describe('ProfileListItem', () => {
  it('프로필 이름과 날짜를 표시한다', () => {
    const profile = makeProfile();
    render(<ProfileListItem profile={profile} onSelect={() => {}} />);

    expect(screen.getByText('테스트 프로필')).toBeInTheDocument();
    expect(screen.getByText('2024-06-20')).toBeInTheDocument();
  });

  it('100자 이하 설명은 그대로 표시한다', () => {
    const description = '짧은 설명입니다.';
    const profile = makeProfile({ description });
    render(<ProfileListItem profile={profile} onSelect={() => {}} />);

    expect(screen.getByText(description)).toBeInTheDocument();
  });

  it('100자 초과 설명을 말줄임 처리한다', () => {
    const longDescription = 'A'.repeat(150);
    const profile = makeProfile({ description: longDescription });
    render(<ProfileListItem profile={profile} onSelect={() => {}} />);

    const expected = 'A'.repeat(100) + '...';
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it('기본 프로필이면 "기본" 배지를 표시한다', () => {
    const profile = makeProfile({ is_default: true });
    render(<ProfileListItem profile={profile} onSelect={() => {}} />);

    expect(screen.getByTestId('default-badge')).toBeInTheDocument();
    expect(screen.getByText('기본')).toBeInTheDocument();
  });

  it('기본 프로필이 아니면 배지를 표시하지 않는다', () => {
    const profile = makeProfile({ is_default: false });
    render(<ProfileListItem profile={profile} onSelect={() => {}} />);

    expect(screen.queryByTestId('default-badge')).not.toBeInTheDocument();
  });

  it('클릭 시 onSelect를 프로필 ID와 함께 호출한다', () => {
    const onSelect = vi.fn();
    const profile = makeProfile({ id: 42 });
    render(<ProfileListItem profile={profile} onSelect={onSelect} />);

    fireEvent.click(screen.getByTestId('profile-item-42'));
    expect(onSelect).toHaveBeenCalledWith(42);
  });
});

describe('truncateDescription', () => {
  it('100자 이하 텍스트는 그대로 반환한다', () => {
    const text = '짧은 텍스트';
    expect(truncateDescription(text)).toBe(text);
  });

  it('정확히 100자는 그대로 반환한다', () => {
    const text = 'X'.repeat(100);
    expect(truncateDescription(text)).toBe(text);
  });

  it('101자 이상이면 100자 + "..." 으로 잘린다', () => {
    const text = 'Y'.repeat(101);
    expect(truncateDescription(text)).toBe('Y'.repeat(100) + '...');
  });

  it('빈 문자열은 빈 문자열을 반환한다', () => {
    expect(truncateDescription('')).toBe('');
  });
});
