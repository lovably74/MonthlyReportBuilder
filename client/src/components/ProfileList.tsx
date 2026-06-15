import { useProfileStore } from '../stores/profileStore';
import { ProfileListItem } from './ProfileListItem';
import { EmptyProfileState } from './EmptyProfileState';
import type { Profile } from '../types/profile';

export interface ProfileListProps {
  onCreate?: () => void;
}

/**
 * 프로필 목록을 정렬하여 반환한다.
 * 기본 프로필을 최상단에, 나머지는 updated_at 내림차순으로 정렬한다.
 */
export function sortProfiles(profiles: Profile[]): Profile[] {
  const defaultProfiles = profiles.filter((p) => p.is_default);
  const otherProfiles = profiles
    .filter((p) => !p.is_default)
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
  return [...defaultProfiles, ...otherProfiles];
}

/**
 * 프로필 목록 컴포넌트
 * - 로딩 중일 때 스피너 표시
 * - 프로필이 없을 때 EmptyProfileState 표시
 * - 기본 프로필 최상단, 나머지 updated_at 내림차순 정렬
 */
export function ProfileList({ onCreate }: ProfileListProps) {
  const profiles = useProfileStore((state) => state.profiles);
  const isLoading = useProfileStore((state) => state.isLoading);
  const selectProfile = useProfileStore((state) => state.selectProfile);

  if (isLoading) {
    return (
      <div className="profile-list profile-list--loading" data-testid="profile-list-loading">
        <span className="profile-list__spinner" aria-label="로딩 중">⏳</span>
      </div>
    );
  }

  if (profiles.length === 0) {
    return <EmptyProfileState onCreate={onCreate} />;
  }

  const sorted = sortProfiles(profiles);

  return (
    <div className="profile-list" data-testid="profile-list">
      {sorted.map((profile) => (
        <ProfileListItem
          key={profile.id}
          profile={profile}
          onSelect={selectProfile}
        />
      ))}
    </div>
  );
}

export default ProfileList;
