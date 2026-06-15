import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useConnectionStore } from '@/stores/connectionStore';
import {
  fetchProfiles,
  createProfile,
  updateProfile,
  deleteProfile,
  copyProfile,
  setDefaultProfile,
  exportProfile,
  importProfile,
  ApiError,
  NetworkError,
} from '@/api/profileApi';

const TEST_SERVER_URL = 'http://192.168.1.10:8741';
const TEST_SERVER_ID = 'test-server-uuid-1234';

describe('profileApi', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);

    // Set up connection store with server info
    useConnectionStore.setState({
      serverUrl: TEST_SERVER_URL,
      serverId: TEST_SERVER_ID,
      status: 'connected',
      lastPingAt: new Date().toISOString(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    useConnectionStore.setState({
      serverUrl: null,
      serverId: null,
      status: 'disconnected',
      lastPingAt: null,
    });
  });

  describe('X-Server-ID header', () => {
    it('should include X-Server-ID header in fetchProfiles', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ profiles: [], total: 0 }),
      });

      await fetchProfiles();

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in createProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1, name: 'Test', description: '', is_default: true, created_at: '', updated_at: '' }),
      });

      await createProfile({ name: 'Test' });

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in deleteProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve(undefined),
      });

      await deleteProfile(1);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/1`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in copyProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 2, name: 'Test (복사본)', description: '', is_default: false, created_at: '', updated_at: '' }),
      });

      await copyProfile(1);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/1/copy`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in setDefaultProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1, name: 'Test', description: '', is_default: true, created_at: '', updated_at: '' }),
      });

      await setDefaultProfile(1);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/1/default`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in exportProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ version: '1.0', profile: { name: 'Test' } }),
      });

      await exportProfile(1);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/1/export`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });

    it('should include X-Server-ID header in importProfile', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 3, name: 'Imported', description: '', is_default: false, created_at: '', updated_at: '' }),
      });

      await importProfile({ profile: { name: 'Imported' } });

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/import`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Server-ID': TEST_SERVER_ID,
          }),
        }),
      );
    });
  });

  describe('fetchProfiles', () => {
    it('should return profile list on success', async () => {
      const mockResponse = {
        profiles: [
          { id: 1, name: '현장A', description: '설명', is_default: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-02T00:00:00Z' },
        ],
        total: 1,
      };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await fetchProfiles();
      expect(result).toEqual(mockResponse);
      expect(result.profiles).toHaveLength(1);
      expect(result.total).toBe(1);
    });

    it('should call GET /api/v1/profiles', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ profiles: [], total: 0 }),
      });

      await fetchProfiles();

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles`,
        expect.objectContaining({ method: 'GET' }),
      );
    });
  });

  describe('createProfile', () => {
    it('should return created profile on success', async () => {
      const mockProfile = { id: 1, name: '현장B', description: '새 프로필', is_default: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProfile),
      });

      const result = await createProfile({ name: '현장B', description: '새 프로필' });
      expect(result).toEqual(mockProfile);
    });

    it('should send POST with JSON body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 1, name: 'X', description: '', is_default: true, created_at: '', updated_at: '' }),
      });

      await createProfile({ name: 'X', description: '설명' });

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'X', description: '설명' }),
        }),
      );
    });
  });

  describe('updateProfile', () => {
    it('should return updated profile on success', async () => {
      const mockProfile = { id: 1, name: '수정됨', description: '', is_default: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-02T00:00:00Z' };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProfile),
      });

      const result = await updateProfile(1, { name: '수정됨' });
      expect(result).toEqual(mockProfile);
    });

    it('should send PUT to /api/v1/profiles/:id', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 5, name: 'Y', description: '', is_default: false, created_at: '', updated_at: '' }),
      });

      await updateProfile(5, { name: 'Y' });

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/5`,
        expect.objectContaining({ method: 'PUT' }),
      );
    });
  });

  describe('deleteProfile', () => {
    it('should complete without error on 204 response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve(undefined),
      });

      await expect(deleteProfile(3)).resolves.toBeUndefined();
    });

    it('should send DELETE to /api/v1/profiles/:id', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve(undefined),
      });

      await deleteProfile(7);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/7`,
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('copyProfile', () => {
    it('should return copied profile on success', async () => {
      const mockCopy = { id: 2, name: '현장A (복사본)', description: '설명', is_default: false, created_at: '2024-01-03T00:00:00Z', updated_at: '2024-01-03T00:00:00Z' };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockCopy),
      });

      const result = await copyProfile(1);
      expect(result).toEqual(mockCopy);
      expect(result.is_default).toBe(false);
    });

    it('should send POST to /api/v1/profiles/:id/copy', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 2, name: 'Copy', description: '', is_default: false, created_at: '', updated_at: '' }),
      });

      await copyProfile(4);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/4/copy`,
        expect.objectContaining({ method: 'POST' }),
      );
    });
  });

  describe('setDefaultProfile', () => {
    it('should return profile with is_default=true on success', async () => {
      const mockProfile = { id: 2, name: '현장B', description: '', is_default: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-04T00:00:00Z' };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProfile),
      });

      const result = await setDefaultProfile(2);
      expect(result.is_default).toBe(true);
    });

    it('should send PUT to /api/v1/profiles/:id/default', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 2, name: 'Test', description: '', is_default: true, created_at: '', updated_at: '' }),
      });

      await setDefaultProfile(2);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/2/default`,
        expect.objectContaining({ method: 'PUT' }),
      );
    });
  });

  describe('exportProfile', () => {
    it('should return export data on success', async () => {
      const mockExport = { version: '1.0', exported_at: '2024-01-01T00:00:00Z', profile: { name: '현장A', description: '설명' }, settings: {} };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockExport),
      });

      const result = await exportProfile(1);
      expect(result).toEqual(mockExport);
    });

    it('should send GET to /api/v1/profiles/:id/export', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      await exportProfile(3);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/3/export`,
        expect.objectContaining({ method: 'GET' }),
      );
    });
  });

  describe('importProfile', () => {
    it('should return imported profile on success', async () => {
      const mockProfile = { id: 4, name: '가져온 프로필', description: '외부 설정', is_default: false, created_at: '2024-01-05T00:00:00Z', updated_at: '2024-01-05T00:00:00Z' };

      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockProfile),
      });

      const importData = { version: '1.0', profile: { name: '가져온 프로필', description: '외부 설정' } };
      const result = await importProfile(importData);
      expect(result).toEqual(mockProfile);
    });

    it('should send POST to /api/v1/profiles/import with JSON body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 4, name: 'Imported', description: '', is_default: false, created_at: '', updated_at: '' }),
      });

      const importData = { version: '1.0', profile: { name: 'Imported' } };
      await importProfile(importData);

      expect(mockFetch).toHaveBeenCalledWith(
        `${TEST_SERVER_URL}/api/v1/profiles/import`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(importData),
        }),
      );
    });
  });

  describe('NetworkError handling', () => {
    it('should throw NetworkError when fetch throws TypeError', async () => {
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

      await expect(fetchProfiles()).rejects.toThrow(NetworkError);
      await expect(fetchProfiles()).rejects.toThrow('서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.');
    });

    it('should throw NetworkError on general network failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      await expect(createProfile({ name: 'Test' })).rejects.toThrow(NetworkError);
    });

    it('should throw NetworkError for AbortError', async () => {
      mockFetch.mockRejectedValue(new DOMException('The operation was aborted.', 'AbortError'));

      await expect(updateProfile(1, { name: 'X' })).rejects.toThrow(NetworkError);
    });
  });

  describe('ApiError handling', () => {
    it('should throw ApiError with parsed error fields on 409 conflict', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 409,
        json: () => Promise.resolve({
          error_code: 'PROFILE_NAME_DUPLICATE',
          message: '동일한 이름의 프로필이 이미 존재합니다.',
          field: 'name',
        }),
      });

      try {
        await createProfile({ name: '중복이름' });
        expect.fail('should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        const apiError = error as ApiError;
        expect(apiError.statusCode).toBe(409);
        expect(apiError.errorCode).toBe('PROFILE_NAME_DUPLICATE');
        expect(apiError.message).toBe('동일한 이름의 프로필이 이미 존재합니다.');
        expect(apiError.field).toBe('name');
      }
    });

    it('should throw ApiError with parsed error fields on 404 not found', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({
          error_code: 'PROFILE_NOT_FOUND',
          message: '해당 프로필을 찾을 수 없습니다.',
          field: null,
        }),
      });

      try {
        await updateProfile(999, { name: 'X' });
        expect.fail('should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        const apiError = error as ApiError;
        expect(apiError.statusCode).toBe(404);
        expect(apiError.errorCode).toBe('PROFILE_NOT_FOUND');
        expect(apiError.field).toBeNull();
      }
    });

    it('should throw ApiError with parsed error fields on 422 validation error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 422,
        json: () => Promise.resolve({
          error_code: 'PROFILE_NAME_REQUIRED',
          message: '프로필명은 필수 입력값입니다.',
          field: 'name',
        }),
      });

      try {
        await createProfile({ name: '' });
        expect.fail('should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        const apiError = error as ApiError;
        expect(apiError.statusCode).toBe(422);
        expect(apiError.errorCode).toBe('PROFILE_NAME_REQUIRED');
        expect(apiError.field).toBe('name');
      }
    });

    it('should throw ApiError with defaults when response body is not JSON', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new SyntaxError('Unexpected token')),
      });

      try {
        await fetchProfiles();
        expect.fail('should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        const apiError = error as ApiError;
        expect(apiError.statusCode).toBe(500);
        expect(apiError.errorCode).toBe('UNKNOWN_ERROR');
        expect(apiError.message).toContain('500');
      }
    });

    it('should throw ApiError on 400 bad request', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({
          error_code: 'PROFILE_LAST_DELETE',
          message: '최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다.',
        }),
      });

      try {
        await deleteProfile(1);
        expect.fail('should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        const apiError = error as ApiError;
        expect(apiError.statusCode).toBe(400);
        expect(apiError.errorCode).toBe('PROFILE_LAST_DELETE');
      }
    });
  });
});
