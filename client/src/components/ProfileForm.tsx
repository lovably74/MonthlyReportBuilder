import { useState, useCallback, useEffect } from 'react';

export interface ProfileFormProps {
  mode: 'create' | 'edit';
  initialValues?: { name: string; description: string };
  onSubmit: (data: { name: string; description: string }) => Promise<void>;
  onCancel?: () => void;
}

interface FormErrors {
  name?: string;
  description?: string;
}

const NAME_MAX_LENGTH = 50;
const DESCRIPTION_MAX_LENGTH = 200;

/**
 * 프로필 생성/수정 공용 폼 컴포넌트
 *
 * - name: 필수, 1~50자 (공백 제거 후 검증)
 * - description: 선택, 0~200자
 * - 실시간 유효성 검증 및 에러 메시지 표시
 * - 성공 시 알림 토스트 표시 (onSubmit에서 처리)
 *
 * Requirements: 1.1~1.8, 2.1~2.6
 */
export function ProfileForm({ mode, initialValues, onSubmit, onCancel }: ProfileFormProps) {
  const [name, setName] = useState(initialValues?.name ?? '');
  const [description, setDescription] = useState(initialValues?.description ?? '');
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ name: boolean; description: boolean }>({
    name: false,
    description: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // initialValues 변경 시 폼 값 동기화 (edit 모드에서 데이터 로드 후)
  useEffect(() => {
    if (initialValues) {
      setName(initialValues.name);
      setDescription(initialValues.description);
    }
  }, [initialValues]);

  const validateName = useCallback((value: string): string | undefined => {
    const trimmed = value.trim();
    if (!trimmed) {
      return '프로필명은 필수 입력값입니다.';
    }
    if (trimmed.length > NAME_MAX_LENGTH) {
      return '프로필명은 50자를 초과할 수 없습니다.';
    }
    return undefined;
  }, []);

  const validateDescription = useCallback((value: string): string | undefined => {
    if (value.length > DESCRIPTION_MAX_LENGTH) {
      return '설명은 200자를 초과할 수 없습니다.';
    }
    return undefined;
  }, []);

  const validate = useCallback((): FormErrors => {
    return {
      name: validateName(name),
      description: validateDescription(description),
    };
  }, [name, description, validateName, validateDescription]);

  const isFormValid = useCallback((): boolean => {
    const currentErrors = validate();
    return !currentErrors.name && !currentErrors.description;
  }, [validate]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setName(value);
    if (touched.name) {
      setErrors((prev) => ({ ...prev, name: validateName(value) }));
    }
  };

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setDescription(value);
    if (touched.description) {
      setErrors((prev) => ({ ...prev, description: validateDescription(value) }));
    }
  };

  const handleNameBlur = () => {
    setTouched((prev) => ({ ...prev, name: true }));
    setErrors((prev) => ({ ...prev, name: validateName(name) }));
  };

  const handleDescriptionBlur = () => {
    setTouched((prev) => ({ ...prev, description: true }));
    setErrors((prev) => ({ ...prev, description: validateDescription(description) }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 전체 유효성 검증
    const formErrors = validate();
    setErrors(formErrors);
    setTouched({ name: true, description: true });

    if (formErrors.name || formErrors.description) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({ name: name.trim(), description });
    } finally {
      setIsSubmitting(false);
    }
  };

  const nameRemaining = NAME_MAX_LENGTH - name.trim().length;
  const descriptionRemaining = DESCRIPTION_MAX_LENGTH - description.length;

  return (
    <form
      className="profile-form"
      onSubmit={handleSubmit}
      noValidate
      data-testid="profile-form"
    >
      <h2 className="profile-form__title">
        {mode === 'create' ? '프로필 생성' : '프로필 수정'}
      </h2>

      {/* Name field */}
      <div className="profile-form__field">
        <label htmlFor="profile-name" className="profile-form__label">
          프로필명 <span className="profile-form__required">*</span>
        </label>
        <input
          id="profile-name"
          type="text"
          className={`profile-form__input ${errors.name && touched.name ? 'profile-form__input--error' : ''}`}
          value={name}
          onChange={handleNameChange}
          onBlur={handleNameBlur}
          placeholder="프로필명을 입력하세요"
          aria-invalid={!!(errors.name && touched.name)}
          aria-describedby="profile-name-error profile-name-count"
          disabled={isSubmitting}
          data-testid="profile-name-input"
        />
        <div className="profile-form__meta">
          {errors.name && touched.name && (
            <span
              id="profile-name-error"
              className="profile-form__error"
              role="alert"
              data-testid="profile-name-error"
            >
              {errors.name}
            </span>
          )}
          <span
            id="profile-name-count"
            className={`profile-form__count ${nameRemaining < 0 ? 'profile-form__count--over' : ''}`}
            data-testid="profile-name-count"
          >
            {nameRemaining}자 남음
          </span>
        </div>
      </div>

      {/* Description field */}
      <div className="profile-form__field">
        <label htmlFor="profile-description" className="profile-form__label">
          설명
        </label>
        <textarea
          id="profile-description"
          className={`profile-form__textarea ${errors.description && touched.description ? 'profile-form__textarea--error' : ''}`}
          value={description}
          onChange={handleDescriptionChange}
          onBlur={handleDescriptionBlur}
          placeholder="프로필 설명을 입력하세요 (선택)"
          rows={4}
          aria-invalid={!!(errors.description && touched.description)}
          aria-describedby="profile-description-error profile-description-count"
          disabled={isSubmitting}
          data-testid="profile-description-input"
        />
        <div className="profile-form__meta">
          {errors.description && touched.description && (
            <span
              id="profile-description-error"
              className="profile-form__error"
              role="alert"
              data-testid="profile-description-error"
            >
              {errors.description}
            </span>
          )}
          <span
            id="profile-description-count"
            className={`profile-form__count ${descriptionRemaining < 0 ? 'profile-form__count--over' : ''}`}
            data-testid="profile-description-count"
          >
            {descriptionRemaining}자 남음
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="profile-form__actions">
        {onCancel && (
          <button
            type="button"
            className="profile-form__button profile-form__button--cancel"
            onClick={onCancel}
            disabled={isSubmitting}
            data-testid="profile-form-cancel"
          >
            취소
          </button>
        )}
        <button
          type="submit"
          className="profile-form__button profile-form__button--submit"
          disabled={isSubmitting || !isFormValid()}
          data-testid="profile-form-submit"
        >
          {isSubmitting
            ? '저장 중...'
            : mode === 'create'
              ? '생성'
              : '저장'}
        </button>
      </div>
    </form>
  );
}

export default ProfileForm;
