/**
 * 프로필 액션 버튼 그룹 컴포넌트
 * 복사, 내보내기, 삭제 버튼을 제공한다.
 * 서버 연결이 끊어진 상태에서는 버튼이 비활성화된다.
 *
 * Requirements: 3.1, 4.1, 6.1, 6.2, 9.3
 */

export interface ProfileActionsProps {
  profileId: number;
  profileName: string;
  isDisabled?: boolean;
  onCopy: (id: number) => void;
  onExport: (id: number) => void;
  onDelete: (id: number, name: string) => void;
}

/**
 * 프로필 복사, 내보내기, 삭제 액션 버튼 그룹
 */
export function ProfileActions({
  profileId,
  profileName,
  isDisabled = false,
  onCopy,
  onExport,
  onDelete,
}: ProfileActionsProps) {
  const disabledTitle = isDisabled
    ? '서버와 연결이 끊어져 사용할 수 없습니다.'
    : undefined;

  return (
    <div className="profile-actions" data-testid="profile-actions">
      <button
        type="button"
        className="profile-actions__btn profile-actions__btn--copy"
        disabled={isDisabled}
        title={disabledTitle}
        onClick={() => onCopy(profileId)}
        aria-label={`프로필 '${profileName}' 복사`}
      >
        복사
      </button>
      <button
        type="button"
        className="profile-actions__btn profile-actions__btn--export"
        disabled={isDisabled}
        title={disabledTitle}
        onClick={() => onExport(profileId)}
        aria-label={`프로필 '${profileName}' 내보내기`}
      >
        내보내기
      </button>
      <button
        type="button"
        className="profile-actions__btn profile-actions__btn--delete"
        disabled={isDisabled}
        title={disabledTitle}
        onClick={() => onDelete(profileId, profileName)}
        aria-label={`프로필 '${profileName}' 삭제`}
      >
        삭제
      </button>
    </div>
  );
}

export default ProfileActions;
