import { describe, it, expect, beforeEach } from 'vitest';
import { useToastStore } from '@/stores/toastStore';

describe('toastStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useToastStore.setState({ toasts: [] });
  });

  describe('initial state', () => {
    it('should have empty toasts array initially', () => {
      const { toasts } = useToastStore.getState();
      expect(toasts).toEqual([]);
    });
  });

  describe('showSuccess', () => {
    it('should add a success toast to the list', () => {
      useToastStore.getState().showSuccess('프로필이 생성되었습니다.');

      const { toasts } = useToastStore.getState();
      expect(toasts).toHaveLength(1);
      expect(toasts[0].message).toBe('프로필이 생성되었습니다.');
      expect(toasts[0].type).toBe('success');
      expect(toasts[0].id).toBeTruthy();
    });

    it('should generate unique IDs for multiple toasts', () => {
      const store = useToastStore.getState();
      store.showSuccess('첫 번째');
      store.showSuccess('두 번째');

      const { toasts } = useToastStore.getState();
      expect(toasts).toHaveLength(2);
      expect(toasts[0].id).not.toBe(toasts[1].id);
    });
  });

  describe('showError', () => {
    it('should add an error toast to the list', () => {
      useToastStore.getState().showError('프로필 삭제에 실패했습니다.');

      const { toasts } = useToastStore.getState();
      expect(toasts).toHaveLength(1);
      expect(toasts[0].message).toBe('프로필 삭제에 실패했습니다.');
      expect(toasts[0].type).toBe('error');
      expect(toasts[0].id).toBeTruthy();
    });
  });

  describe('dismiss', () => {
    it('should remove the toast with matching id', () => {
      const store = useToastStore.getState();
      store.showSuccess('메시지 1');
      store.showError('메시지 2');

      const toastsBefore = useToastStore.getState().toasts;
      expect(toastsBefore).toHaveLength(2);

      const idToRemove = toastsBefore[0].id;
      useToastStore.getState().dismiss(idToRemove);

      const toastsAfter = useToastStore.getState().toasts;
      expect(toastsAfter).toHaveLength(1);
      expect(toastsAfter[0].id).not.toBe(idToRemove);
    });

    it('should do nothing when dismissing non-existent id', () => {
      useToastStore.getState().showSuccess('남아있는 토스트');

      useToastStore.getState().dismiss('non-existent-id');

      const { toasts } = useToastStore.getState();
      expect(toasts).toHaveLength(1);
    });
  });

  describe('multiple toasts', () => {
    it('should support mixed success and error toasts', () => {
      const store = useToastStore.getState();
      store.showSuccess('성공 메시지');
      store.showError('에러 메시지');
      store.showSuccess('또 다른 성공');

      const { toasts } = useToastStore.getState();
      expect(toasts).toHaveLength(3);
      expect(toasts[0].type).toBe('success');
      expect(toasts[1].type).toBe('error');
      expect(toasts[2].type).toBe('success');
    });
  });
});
