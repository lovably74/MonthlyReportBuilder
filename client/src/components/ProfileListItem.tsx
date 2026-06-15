import type { Profile } from '../types/profile';

export interface ProfileListItemProps {
  profile: Profile;
  onSelect: (id: number) => void;
}

/**
 * 설명 텍스트를 최대 100자로 잘라 말줄임 처리한다.
 */
export function truncateDescription(text: string, maxLength = 100): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * ISO 8601 날짜 문자열을 "YYYY-MM-DD" 형식으로 포맷한다.
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 개별 프로필 항목 컴포넌트
 * 이름, 설명(100자 말줄임), 기본 배지, 수정일을 표시한다.
 */
export function ProfileListItem({ profile, onSelect }: ProfileListItemProps) {
  return (
    <div
      className="profile-list-item"
      data-testid={`profile-item-${profile.id}`}
      onClick={() => onSelect(profile.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(profile.id);
        }
      }}
    >
      <div className="profile-list-item__header">
        <span className="profile-list-item__name">{profile.name}</span>
        {profile.is_default && (
          <span className="profile-list-item__badge" data-testid="default-badge">
            기본
          </span>
        )}
      </div>
      <p className="profile-list-item__description">
        {truncateDescription(profile.description)}
      </p>
      <span className="profile-list-item__date">
        {formatDate(profile.updated_at)}
      </span>
    </div>
  );
}

export default ProfileListItem;
