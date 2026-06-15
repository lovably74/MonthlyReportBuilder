import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProfileList, sortProfiles } from './ProfileList';
import { useProfileStore } from '../stores/profileStore';
import type { Profile } from '../types/profile';

function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return {
    id: 1,
    name: '프로필 1',
    description: '설명',
    is_default: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('ProfileList', () => {
  beforeEach(() => {
    // Reset store state before each test
    useProfileStore.setState({
      profiles: [],
      selectedProfileId: null,
      isLoading: false,
      error: null,
    });
  });

  it('로딩 중일 때 로딩 스피너를 표시한다', () => {
    useProfileStore.setState({ isLoading: true });

    render(<ProfileList />);

    expect(screen.getByTestId('profile-list-loading')).toBeInTheDocument();
  });

  it('프로필이 없을 때 빈 상태를 표시한다', () => {
    useProfileStore.setState({ profiles: [], isLoading: false });

    render(<ProfileList />);

    expect(screen.getByTestId('empty-profile-state')).toBeInTheDocument();
    expect(screen.getByText('등록된 프로필이 없습니다.')).toBeInTheDocument();
  });

  it('프로필 목록을 렌더링한다', () => {
    const profiles: Profile[] = [
      makeProfile({ id: 1, name: '첫 번째', is_default: true }),
      makeProfile({ id: 2, name: '두 번째', is_default: false }),
    ];
    useProfileStore.setState({ profiles, isLoading: false });

    render(<ProfileList />);

    expect(screen.getByTestId('profile-list')).toBeInTheDocument();
    expect(screen.getByText('첫 번째')).toBeInTheDocument();
    expect(screen.getByText('두 번째')).toBeInTheDocument();
  });

  it('항목 클릭 시 selectProfile을 호출한다', () => {
    const profiles: Profile[] = [
      makeProfile({ id: 5, name: '선택용 프로필', is_default: true }),
    ];
    useProfileStore.setState({ profiles, isLoading: false });

    render(<ProfileList />);

    fireEvent.click(screen.getByTestId('profile-item-5'));
    expect(useProfileStore.getState().selectedProfileId).toBe(5);
  });
});

describe('sortProfiles', () => {
  it('기본 프로필을 최상단에 배치한다', () => {
    const profiles: Profile[] = [
      makeProfile({ id: 1, name: 'B', is_default: false, updated_at: '2024-06-01T00:00:00Z' }),
      makeProfile({ id: 2, name: 'A', is_default: true, updated_at: '2024-01-01T00:00:00Z' }),
    ];

    const sorted = sortProfiles(profiles);
    expect(sorted[0].id).toBe(2);
    expect(sorted[0].is_default).toBe(true);
  });

  it('기본 프로필 외 나머지를 updated_at 내림차순으로 정렬한다', () => {
    const profiles: Profile[] = [
      makeProfile({ id: 1, name: '기본', is_default: true, updated_at: '2024-01-01T00:00:00Z' }),
      makeProfile({ id: 2, name: '오래된', is_default: false, updated_at: '2024-02-01T00:00:00Z' }),
      makeProfile({ id: 3, name: '최신', is_default: false, updated_at: '2024-06-01T00:00:00Z' }),
      makeProfile({ id: 4, name: '중간', is_default: false, updated_at: '2024-04-01T00:00:00Z' }),
    ];

    const sorted = sortProfiles(profiles);
    expect(sorted[0].id).toBe(1); // 기본 프로필
    expect(sorted[1].id).toBe(3); // 최신
    expect(sorted[2].id).toBe(4); // 중간
    expect(sorted[3].id).toBe(2); // 오래된
  });
});
