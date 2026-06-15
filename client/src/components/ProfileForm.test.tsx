import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProfileForm, ProfileFormProps } from './ProfileForm';

function renderForm(overrides: Partial<ProfileFormProps> = {}) {
  const defaultProps: ProfileFormProps = {
    mode: 'create',
    onSubmit: vi.fn().mockResolvedValue(undefined),
    onCancel: vi.fn(),
    ...overrides,
  };
  return { ...render(<ProfileForm {...defaultProps} />), props: defaultProps };
}

describe('ProfileForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('create 모드에서 빈 필드로 렌더링된다', () => {
    renderForm({ mode: 'create' });

    expect(screen.getByTestId('profile-name-input')).toHaveValue('');
    expect(screen.getByTestId('profile-description-input')).toHaveValue('');
    expect(screen.getByText('프로필 생성')).toBeInTheDocument();
    expect(screen.getByTestId('profile-form-submit')).toHaveTextContent('생성');
  });

  it('edit 모드에서 초기값이 채워져 렌더링된다', () => {
    renderForm({
      mode: 'edit',
      initialValues: { name: '테스트 프로필', description: '설명 텍스트' },
    });

    expect(screen.getByTestId('profile-name-input')).toHaveValue('테스트 프로필');
    expect(screen.getByTestId('profile-description-input')).toHaveValue('설명 텍스트');
    expect(screen.getByText('프로필 수정')).toBeInTheDocument();
    expect(screen.getByTestId('profile-form-submit')).toHaveTextContent('저장');
  });

  it('빈 이름으로 제출 시 에러 메시지를 표시한다', async () => {
    renderForm({ mode: 'create' });

    // 이름 필드에 포커스 후 빈 채로 blur → 에러 표시
    const nameInput = screen.getByTestId('profile-name-input');
    fireEvent.focus(nameInput);
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(screen.getByTestId('profile-name-error')).toHaveTextContent(
        '프로필명은 필수 입력값입니다.'
      );
    });
  });

  it('50자 초과 이름 입력 시 에러 메시지를 표시한다', async () => {
    renderForm({ mode: 'create' });

    const longName = 'A'.repeat(51);
    const nameInput = screen.getByTestId('profile-name-input');

    fireEvent.change(nameInput, { target: { value: longName } });
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(screen.getByTestId('profile-name-error')).toHaveTextContent(
        '프로필명은 50자를 초과할 수 없습니다.'
      );
    });
  });

  it('200자 초과 설명 입력 시 에러 메시지를 표시한다', async () => {
    renderForm({ mode: 'create' });

    const longDesc = 'B'.repeat(201);
    const descInput = screen.getByTestId('profile-description-input');

    fireEvent.change(descInput, { target: { value: longDesc } });
    fireEvent.blur(descInput);

    await waitFor(() => {
      expect(screen.getByTestId('profile-description-error')).toHaveTextContent(
        '설명은 200자를 초과할 수 없습니다.'
      );
    });
  });

  it('폼이 유효하지 않을 때 제출 버튼이 비활성화된다', () => {
    renderForm({ mode: 'create' });

    // 초기 상태: 이름 비어있음 → invalid
    const submitButton = screen.getByTestId('profile-form-submit');
    expect(submitButton).toBeDisabled();
  });

  it('유효한 데이터로 제출 시 onSubmit이 올바른 데이터로 호출된다', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    renderForm({ mode: 'create', onSubmit });

    const nameInput = screen.getByTestId('profile-name-input');
    const descInput = screen.getByTestId('profile-description-input');

    fireEvent.change(nameInput, { target: { value: '  새 프로필  ' } });
    fireEvent.change(descInput, { target: { value: '설명 입니다' } });
    fireEvent.click(screen.getByTestId('profile-form-submit'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: '새 프로필',
        description: '설명 입니다',
      });
    });
  });

  it('제출 중에는 버튼이 비활성화되고 "저장 중..." 텍스트가 표시된다', async () => {
    let resolveSubmit: () => void;
    const onSubmit = vi.fn().mockImplementation(
      () => new Promise<void>((resolve) => { resolveSubmit = resolve; })
    );
    renderForm({ mode: 'edit', initialValues: { name: '프로필', description: '' }, onSubmit });

    fireEvent.click(screen.getByTestId('profile-form-submit'));

    await waitFor(() => {
      const submitButton = screen.getByTestId('profile-form-submit');
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent('저장 중...');
    });

    // 제출 완료
    resolveSubmit!();

    await waitFor(() => {
      const submitButton = screen.getByTestId('profile-form-submit');
      expect(submitButton).not.toBeDisabled();
      expect(submitButton).toHaveTextContent('저장');
    });
  });

  it('취소 버튼 클릭 시 onCancel이 호출된다', () => {
    const onCancel = vi.fn();
    renderForm({ mode: 'create', onCancel });

    fireEvent.click(screen.getByTestId('profile-form-cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('남은 글자 수 카운트를 표시한다', () => {
    renderForm({ mode: 'create' });

    expect(screen.getByTestId('profile-name-count')).toHaveTextContent('50자 남음');
    expect(screen.getByTestId('profile-description-count')).toHaveTextContent('200자 남음');

    fireEvent.change(screen.getByTestId('profile-name-input'), {
      target: { value: '테스트' },
    });

    expect(screen.getByTestId('profile-name-count')).toHaveTextContent('47자 남음');
  });

  it('blur 이벤트에서 유효성 검증이 트리거된다', async () => {
    renderForm({ mode: 'create' });

    const nameInput = screen.getByTestId('profile-name-input');
    fireEvent.focus(nameInput);
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(screen.getByTestId('profile-name-error')).toHaveTextContent(
        '프로필명은 필수 입력값입니다.'
      );
    });
  });

  it('onCancel이 없으면 취소 버튼이 렌더링되지 않는다', () => {
    renderForm({ mode: 'create', onCancel: undefined });

    expect(screen.queryByTestId('profile-form-cancel')).not.toBeInTheDocument();
  });
});
