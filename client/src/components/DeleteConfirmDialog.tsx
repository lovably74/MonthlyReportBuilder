/**
 * 삭제 확인 대화상자 컴포넌트
 * 프로필 삭제 시 사용자에게 확인을 요청한다.
 *
 * Requirements: 4.1, 4.3
 */

export interface DeleteConfirmDialogProps {
  isOpen: boolean;
  profileName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * 프로필 삭제 확인 대화상자
 * "프로필 '[이름]'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
 */
export function DeleteConfirmDialog({
  isOpen,
  profileName,
  onConfirm,
  onCancel,
}: DeleteConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div
      className="dialog-overlay"
      data-testid="delete-confirm-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
    >
      <div className="dialog">
        <h2 id="delete-dialog-title" className="dialog__title">
          프로필 삭제
        </h2>
        <p className="dialog__message">
          프로필 &apos;{profileName}&apos;을(를) 삭제하시겠습니까? 이 작업은
          되돌릴 수 없습니다.
        </p>
        <div className="dialog__actions">
          <button
            type="button"
            className="dialog__btn dialog__btn--cancel"
            onClick={onCancel}
          >
            취소
          </button>
          <button
            type="button"
            className="dialog__btn dialog__btn--confirm dialog__btn--danger"
            onClick={onConfirm}
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmDialog;
