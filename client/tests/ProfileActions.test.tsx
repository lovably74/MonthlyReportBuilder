import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProfileActions } from '@/components/ProfileActions';
import { DeleteConfirmDialog } from '@/components/DeleteConfirmDialog';
import { ImportDialog } from '@/components/ImportDialog';

describe('ProfileActions component', () => {
  const defaultProps = {
    profileId: 1,
    profileName: '현장A',
    onCopy: vi.fn(),
    onExport: vi.fn(),
    onDelete: vi.fn(),
  };

  it('should render all three buttons (복사, 내보내기, 삭제)', () => {
    render(<ProfileActions {...defaultProps} />);

    expect(screen.getByText('복사')).toBeInTheDocument();
    expect(screen.getByText('내보내기')).toBeInTheDocument();
    expect(screen.getByText('삭제')).toBeInTheDocument();
  });

  it('should call onCopy with profileId when 복사 button is clicked', () => {
    const onCopy = vi.fn();
    render(<ProfileActions {...defaultProps} onCopy={onCopy} />);

    fireEvent.click(screen.getByText('복사'));
    expect(onCopy).toHaveBeenCalledWith(1);
  });

  it('should call onExport with profileId when 내보내기 button is clicked', () => {
    const onExport = vi.fn();
    render(<ProfileActions {...defaultProps} onExport={onExport} />);

    fireEvent.click(screen.getByText('내보내기'));
    expect(onExport).toHaveBeenCalledWith(1);
  });

  it('should call onDelete with profileId and profileName when 삭제 button is clicked', () => {
    const onDelete = vi.fn();
    render(<ProfileActions {...defaultProps} onDelete={onDelete} />);

    fireEvent.click(screen.getByText('삭제'));
    expect(onDelete).toHaveBeenCalledWith(1, '현장A');
  });

  it('should disable all buttons when isDisabled=true', () => {
    render(<ProfileActions {...defaultProps} isDisabled={true} />);

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(3);
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it('should show tooltip on disabled buttons explaining server disconnection', () => {
    render(<ProfileActions {...defaultProps} isDisabled={true} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => {
      expect(btn).toHaveAttribute('title', '서버와 연결이 끊어져 사용할 수 없습니다.');
    });
  });

  it('should not have title attribute when buttons are enabled', () => {
    render(<ProfileActions {...defaultProps} isDisabled={false} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => {
      expect(btn).not.toHaveAttribute('title');
    });
  });
});

describe('DeleteConfirmDialog component', () => {
  const defaultProps = {
    isOpen: true,
    profileName: '테스트 프로필',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('should not render when isOpen is false', () => {
    render(<DeleteConfirmDialog {...defaultProps} isOpen={false} />);

    expect(screen.queryByTestId('delete-confirm-dialog')).not.toBeInTheDocument();
  });

  it('should show correct message with profile name', () => {
    render(<DeleteConfirmDialog {...defaultProps} />);

    expect(
      screen.getByText(
        "프로필 '테스트 프로필'을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
      )
    ).toBeInTheDocument();
  });

  it('should have role=dialog and aria-modal=true for accessibility', () => {
    render(<DeleteConfirmDialog {...defaultProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('should call onConfirm when 삭제 button is clicked', () => {
    const onConfirm = vi.fn();
    render(<DeleteConfirmDialog {...defaultProps} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByText('삭제'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when 취소 button is clicked', () => {
    const onCancel = vi.fn();
    render(<DeleteConfirmDialog {...defaultProps} onCancel={onCancel} />);

    fireEvent.click(screen.getByText('취소'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('should display the dialog title', () => {
    render(<DeleteConfirmDialog {...defaultProps} />);

    expect(screen.getByText('프로필 삭제')).toBeInTheDocument();
  });
});

describe('ImportDialog component', () => {
  const defaultProps = {
    isOpen: true,
    conflictName: '기존 프로필',
    onNewName: vi.fn(),
    onCancel: vi.fn(),
  };

  it('should not render when isOpen is false', () => {
    render(<ImportDialog {...defaultProps} isOpen={false} />);

    expect(screen.queryByTestId('import-dialog')).not.toBeInTheDocument();
  });

  it('should show conflict message with the conflicting name', () => {
    render(<ImportDialog {...defaultProps} />);

    expect(
      screen.getByText(
        "프로필 '기존 프로필'이(가) 이미 존재합니다. 새 이름을 입력해 주세요."
      )
    ).toBeInTheDocument();
  });

  it('should have an input field for new profile name', () => {
    render(<ImportDialog {...defaultProps} />);

    const input = screen.getByTestId('import-dialog-input');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', '새 프로필명 입력');
  });

  it('should have role=dialog and aria-modal=true for accessibility', () => {
    render(<ImportDialog {...defaultProps} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('should call onCancel when 취소 button is clicked', () => {
    const onCancel = vi.fn();
    render(<ImportDialog {...defaultProps} onCancel={onCancel} />);

    fireEvent.click(screen.getByText('취소'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('should disable 저장 button when input is empty', () => {
    render(<ImportDialog {...defaultProps} />);

    const saveBtn = screen.getByText('저장');
    expect(saveBtn).toBeDisabled();
  });

  it('should enable 저장 button when input has content', () => {
    render(<ImportDialog {...defaultProps} />);

    const input = screen.getByTestId('import-dialog-input');
    fireEvent.change(input, { target: { value: '새 이름' } });

    const saveBtn = screen.getByText('저장');
    expect(saveBtn).not.toBeDisabled();
  });

  it('should call onNewName with trimmed input when 저장 is clicked', () => {
    const onNewName = vi.fn();
    render(<ImportDialog {...defaultProps} onNewName={onNewName} />);

    const input = screen.getByTestId('import-dialog-input');
    fireEvent.change(input, { target: { value: '  새 프로필  ' } });
    fireEvent.click(screen.getByText('저장'));

    expect(onNewName).toHaveBeenCalledWith('새 프로필');
  });

  it('should limit input to 50 characters', () => {
    render(<ImportDialog {...defaultProps} />);

    const input = screen.getByTestId('import-dialog-input');
    expect(input).toHaveAttribute('maxLength', '50');
  });
});
