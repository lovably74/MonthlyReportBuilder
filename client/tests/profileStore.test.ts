import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useProfileStore } from '@/stores/profileStore';
import { useConnectionStore } from '@/stores/connectionStore';
import * as api from '@/api/profileApi';
import { ApiError, NetworkError } from '@/api/profileApi';
import { profileCache } from '@/cache/profileCache';
import type { Profile } from '@/types/profile';

vi.mock('@/api/profileApi', () => ({
  fetchProfiles: vi.fn(),
  createProfile: vi.fn(),
  updateProfile: vi.fn(),
  deleteProfile: vi.fn(),
  copyProfile: vi.fn(),
  setDefaultProfile: vi.fn(),
  exportProfile: vi.fn(),
  importProfile: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      public statusCode: number,
      public errorCode: string,
      message: string,
      public field?: string | null,
    ) {
      super(message);
      this.name = 'ApiError';
    }
  },
  NetworkError: class NetworkError extends Error {
    constructor() {
      super('서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.');
      this.name = 'NetworkError';
    }
  },
}));

vi.mock('@/cache/profileCache', () => ({
  profileCache: {
    save: vi.fn(),
    load: vi.fn(),
    clear: vi.fn(),
    isValid: vi.fn(),
  },
}));

const MOCK_PROFILES: Profile[] = [
  {
    id: 1,
    name: '현장A',
    description: '기본 프로필',
    is_default: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
  },
  {
    id: 2,
    name: '현장B',
    description: '두 번째',
    is_default: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-09T00:00:00Z',
  },
];

describe('profileStore', () => {
  beforeEach(() => {
    // Reset stores to initial state
    useProfileStore.setState({
      profiles: [],
      selectedProfileId: null,
      isLoading: false,
      error: null,
    });

    useConnectionStore.setState({
      status: 'connected',
      serverUrl: 'http://192.168.1.10:8741',
      serverId: 'test-server-uuid',
      lastPingAt: new Date().toISOString(),
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('fetchProfiles', () => {
    it('should load profiles from API when connected', async () => {
      vi.mocked(api.fetchProfiles).mockResolvedValue({
        profiles: MOCK_PROFILES,
        total: 2,
      });

      await useProfileStore.getState().fetchProfiles();

      const state = useProfileStore.getState();
      expect(state.profiles).toEqual(MOCK_PROFILES);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(api.fetchProfiles).toHaveBeenCalledTimes(1);
    });

    it('should save fetched profiles to cache when connected', async () => {
      vi.mocked(api.fetchProfiles).mockResolvedValue({
        profiles: MOCK_PROFILES,
        total: 2,
      });

      await useProfileStore.getState().fetchProfiles();

      expect(profileCache.save).toHaveBeenCalledWith(MOCK_PROFILES);
    });

    it('should load profiles from cache when disconnected', async () => {
      useConnectionStore.setState({ status: 'disconnected' });
      vi.mocked(profileCache.load).mockReturnValue(MOCK_PROFILES);

      await useProfileStore.getState().fetchProfiles();

      const state = useProfileStore.getState();
      expect(state.profiles).toEqual(MOCK_PROFILES);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(api.fetchProfiles).not.toHaveBeenCalled();
      expect(profileCache.load).toHaveBeenCalled();
    });

    it('should return empty array when disconnected and no cache', async () => {
      useConnectionStore.setState({ status: 'disconnected' });
      vi.mocked(profileCache.load).mockReturnValue(null);

      await useProfileStore.getState().fetchProfiles();

      const state = useProfileStore.getState();
      expect(state.profiles).toEqual([]);
      expect(state.isLoading).toBe(false);
    });

    it('should set isLoading to true during fetch', async () => {
      let loadingDuringFetch = false;

      vi.mocked(api.fetchProfiles).mockImplementation(async () => {
        loadingDuringFetch = useProfileStore.getState().isLoading;
        return { profiles: [], total: 0 };
      });

      await useProfileStore.getState().fetchProfiles();

      expect(loadingDuringFetch).toBe(true);
      expect(useProfileStore.getState().isLoading).toBe(false);
    });

    it('should fall back to cache on NetworkError', async () => {
      vi.mocked(api.fetchProfiles).mockRejectedValue(new NetworkError());
      vi.mocked(profileCache.load).mockReturnValue(MOCK_PROFILES);

      await useProfileStore.getState().fetchProfiles();

      const state = useProfileStore.getState();
      expect(state.profiles).toEqual(MOCK_PROFILES);
      expect(state.error).toBe('서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.');
      expect(state.isLoading).toBe(false);
    });

    it('should set error on API failure', async () => {
      vi.mocked(api.fetchProfiles).mockRejectedValue(
        new ApiError(500, 'DATABASE_ERROR', '데이터베이스 접근에 실패했습니다.'),
      );

      await useProfileStore.getState().fetchProfiles();

      const state = useProfileStore.getState();
      expect(state.error).toBe('데이터베이스 접근에 실패했습니다.');
      expect(state.isLoading).toBe(false);
    });
  });

  describe('write operations blocked when disconnected', () => {
    const DISCONNECTED_MSG = '서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.';

    beforeEach(() => {
      useConnectionStore.setState({ status: 'disconnected' });
    });

    it('createProfile should set error when disconnected', async () => {
      await useProfileStore.getState().createProfile({ name: 'New' });

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.createProfile).not.toHaveBeenCalled();
    });

    it('updateProfile should set error when disconnected', async () => {
      await useProfileStore.getState().updateProfile(1, { name: 'Updated' });

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.updateProfile).not.toHaveBeenCalled();
    });

    it('deleteProfile should set error when disconnected', async () => {
      await useProfileStore.getState().deleteProfile(1);

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.deleteProfile).not.toHaveBeenCalled();
    });

    it('copyProfile should set error when disconnected', async () => {
      await useProfileStore.getState().copyProfile(1);

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.copyProfile).not.toHaveBeenCalled();
    });

    it('setDefaultProfile should set error when disconnected', async () => {
      await useProfileStore.getState().setDefaultProfile(1);

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.setDefaultProfile).not.toHaveBeenCalled();
    });

    it('importProfile should set error when disconnected', async () => {
      await useProfileStore.getState().importProfile({ profile: { name: 'X' } });

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.importProfile).not.toHaveBeenCalled();
    });

    it('exportProfile should set error when disconnected', async () => {
      const result = await useProfileStore.getState().exportProfile(1);

      expect(useProfileStore.getState().error).toBe(DISCONNECTED_MSG);
      expect(api.exportProfile).not.toHaveBeenCalled();
      expect(result).toEqual({});
    });
  });

  describe('createProfile when connected', () => {
    it('should call API and re-fetch profiles on success', async () => {
      vi.mocked(api.createProfile).mockResolvedValue({
        id: 3,
        name: 'New',
        description: '',
        is_default: false,
        created_at: '2024-01-11T00:00:00Z',
        updated_at: '2024-01-11T00:00:00Z',
      });
      vi.mocked(api.fetchProfiles).mockResolvedValue({
        profiles: [...MOCK_PROFILES, { id: 3, name: 'New', description: '', is_default: false, created_at: '2024-01-11T00:00:00Z', updated_at: '2024-01-11T00:00:00Z' }],
        total: 3,
      });

      await useProfileStore.getState().createProfile({ name: 'New' });

      expect(api.createProfile).toHaveBeenCalledWith({ name: 'New' });
      expect(api.fetchProfiles).toHaveBeenCalled();
      expect(useProfileStore.getState().error).toBeNull();
    });

    it('should set error on API failure', async () => {
      vi.mocked(api.createProfile).mockRejectedValue(
        new ApiError(409, 'PROFILE_NAME_DUPLICATE', '동일한 이름의 프로필이 이미 존재합니다.'),
      );

      await useProfileStore.getState().createProfile({ name: 'Duplicate' });

      expect(useProfileStore.getState().error).toBe('동일한 이름의 프로필이 이미 존재합니다.');
    });
  });

  describe('deleteProfile when connected', () => {
    it('should clear selectedProfileId if deleted profile was selected', async () => {
      useProfileStore.setState({ selectedProfileId: 1 });
      vi.mocked(api.deleteProfile).mockResolvedValue(undefined);
      vi.mocked(api.fetchProfiles).mockResolvedValue({
        profiles: [MOCK_PROFILES[1]],
        total: 1,
      });

      await useProfileStore.getState().deleteProfile(1);

      expect(useProfileStore.getState().selectedProfileId).toBeNull();
    });

    it('should keep selectedProfileId if different profile was deleted', async () => {
      useProfileStore.setState({ selectedProfileId: 1 });
      vi.mocked(api.deleteProfile).mockResolvedValue(undefined);
      vi.mocked(api.fetchProfiles).mockResolvedValue({
        profiles: [MOCK_PROFILES[0]],
        total: 1,
      });

      await useProfileStore.getState().deleteProfile(2);

      expect(useProfileStore.getState().selectedProfileId).toBe(1);
    });
  });

  describe('exportProfile when connected', () => {
    it('should return export data on success', async () => {
      const exportData = { version: '1.0', profile: { name: '현장A' }, settings: {} };
      vi.mocked(api.exportProfile).mockResolvedValue(exportData);

      const result = await useProfileStore.getState().exportProfile(1);

      expect(result).toEqual(exportData);
      expect(useProfileStore.getState().error).toBeNull();
    });

    it('should set error and return empty object on failure', async () => {
      vi.mocked(api.exportProfile).mockRejectedValue(
        new ApiError(404, 'PROFILE_NOT_FOUND', '해당 프로필을 찾을 수 없습니다.'),
      );

      const result = await useProfileStore.getState().exportProfile(999);

      expect(result).toEqual({});
      expect(useProfileStore.getState().error).toBe('해당 프로필을 찾을 수 없습니다.');
    });
  });

  describe('selectProfile', () => {
    it('should update selectedProfileId', () => {
      useProfileStore.getState().selectProfile(5);
      expect(useProfileStore.getState().selectedProfileId).toBe(5);
    });

    it('should accept null to deselect', () => {
      useProfileStore.setState({ selectedProfileId: 3 });
      useProfileStore.getState().selectProfile(null);
      expect(useProfileStore.getState().selectedProfileId).toBeNull();
    });
  });

  describe('clearError', () => {
    it('should reset error to null', () => {
      useProfileStore.setState({ error: '이전 에러' });
      useProfileStore.getState().clearError();
      expect(useProfileStore.getState().error).toBeNull();
    });
  });
});
