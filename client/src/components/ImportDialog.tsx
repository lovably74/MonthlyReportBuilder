/**
 * 가져오기 이름 충돌 해결 대화상자 컴포넌트
 * 가져오기 시 프로필명이 이미 존재하면 새 이름을 입력받는다.
 *
 * Requirements: 7.5
 */
import { useState } from 'react';

export interface ImportDialogProps {
  isOpen: boolean;
  conflictName: string;
  onNewName: (name: string) => void;
  onCancel: () => void;
}

/**
 * 가져오기 시 이름 충돌 해결 대화상자
 * 사용자가 새 프로필명을 입력할 수 있도록 한다.
 */
export function ImportDialog({
  isOpen,
  conflictName,
  onNewName,
  onCancel,
}: ImportDialogProps) {
  const [newName, setNewName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = () => {
    const trimmed = newName.trim();
    if (trimmed.length > 0) {
      onNewName(trimmed);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div
      className="dialog-overlay"
      data-testid="import-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="import-dialog-title"
    >
      <div className="dialog">
        <h2 id="import-dialog-title" className="dialog__title">
          이름 충돌
        </h2>
        <p className="dialog__message">
          프로필 &apos;{conflictName}&apos;이(가) 이미 존재합니다. 새 이름을
          입력해 주세요.
        </p>
        <input
          type="text"
          className="dialog__input"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="새 프로필명 입력"
          maxLength={50}
          aria-label="새 프로필명"
          data-testid="import-dialog-input"
          autoFocus
        />
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
            className="dialog__btn dialog__btn--confirm"
            onClick={handleSubmit}
            disabled={newName.trim().length === 0}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}

export default ImportDialog;
