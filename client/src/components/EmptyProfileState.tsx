export interface EmptyProfileStateProps {
  onCreate?: () => void;
}

/**
 * 프로필이 없을 때 표시하는 빈 상태 안내 컴포넌트
 * 생성 유도 메시지와 버튼을 포함한다.
 */
export function EmptyProfileState({ onCreate }: EmptyProfileStateProps) {
  return (
    <div className="empty-profile-state" data-testid="empty-profile-state">
      <p className="empty-profile-state__message">
        등록된 프로필이 없습니다.
      </p>
      <button
        className="empty-profile-state__button"
        onClick={onCreate}
        type="button"
      >
        새 프로필 생성
      </button>
    </div>
  );
}

export default EmptyProfileState;
