import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { profileCache } from '@/cache/profileCache';
import type { Profile } from '@/types/profile';

const mockProfiles: Profile[] = [
  {
    id: 1,
    name: '기본 프로필',
    description: '기본 설명',
    is_default: true,
    created_at: '2024-01-01T00:00:00.000Z',
    updated_at: '2024-01-15T10:30:00.000Z',
  },
  {
    id: 2,
    name: '현장A 프로필',
    description: '현장A 전용 보고서 설정',
    is_default: false,
    created_at: '2024-01-05T00:00:00.000Z',
    updated_at: '2024-01-20T14:00:00.000Z',
  },
];

describe('profileCache', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
    vi.useRealTimers();
  });

  describe('save and load round-trip', () => {
    it('should save profiles and load them back correctly', () => {
      profileCache.save(mockProfiles);
      const loaded = profileCache.load();

      expect(loaded).toEqual(mockProfiles);
    });

    it('should save an empty array and load it back', () => {
      profileCache.save([]);
      const loaded = profileCache.load();

      expect(loaded).toEqual([]);
    });

    it('should overwrite existing cache on subsequent save', () => {
      profileCache.save(mockProfiles);
      const updatedProfiles = [mockProfiles[0]];
      profileCache.save(updatedProfiles);

      const loaded = profileCache.load();
      expect(loaded).toEqual(updatedProfiles);
    });
  });

  describe('load', () => {
    it('should return null when cache is empty', () => {
      const loaded = profileCache.load();
      expect(loaded).toBeNull();
    });

    it('should return null when stored data is not valid JSON', () => {
      localStorage.setItem('cm_report_profiles_cache', 'not valid json{{{');
      const loaded = profileCache.load();
      expect(loaded).toBeNull();
    });

    it('should return null when stored data is not an array', () => {
      localStorage.setItem('cm_report_profiles_cache', JSON.stringify({ not: 'array' }));
      const loaded = profileCache.load();
      expect(loaded).toBeNull();
    });
  });

  describe('getLastCachedAt', () => {
    it('should return null when no cache exists', () => {
      expect(profileCache.getLastCachedAt()).toBeNull();
    });

    it('should return a timestamp string after save', () => {
      profileCache.save(mockProfiles);
      const ts = profileCache.getLastCachedAt();

      expect(ts).not.toBeNull();
      // Should be a valid ISO date string
      expect(new Date(ts!).getTime()).not.toBeNaN();
    });
  });

  describe('clear', () => {
    it('should remove cached profiles and timestamp', () => {
      profileCache.save(mockProfiles);
      profileCache.clear();

      expect(profileCache.load()).toBeNull();
      expect(profileCache.getLastCachedAt()).toBeNull();
    });

    it('should not throw when clearing an empty cache', () => {
      expect(() => profileCache.clear()).not.toThrow();
    });
  });

  describe('isValid', () => {
    it('should return false when no cache exists', () => {
      expect(profileCache.isValid()).toBe(false);
    });

    it('should return true for a freshly saved cache', () => {
      profileCache.save(mockProfiles);
      expect(profileCache.isValid()).toBe(true);
    });

    it('should return false when cache is older than 24 hours', () => {
      vi.useFakeTimers();
      const now = new Date('2024-06-01T12:00:00.000Z');
      vi.setSystemTime(now);

      profileCache.save(mockProfiles);

      // Advance time by 25 hours
      vi.setSystemTime(new Date('2024-06-02T13:00:00.000Z'));

      expect(profileCache.isValid()).toBe(false);
    });

    it('should return true when cache is less than 24 hours old', () => {
      vi.useFakeTimers();
      const now = new Date('2024-06-01T12:00:00.000Z');
      vi.setSystemTime(now);

      profileCache.save(mockProfiles);

      // Advance time by 23 hours
      vi.setSystemTime(new Date('2024-06-02T11:00:00.000Z'));

      expect(profileCache.isValid()).toBe(true);
    });

    it('should return false when timestamp is corrupted', () => {
      localStorage.setItem('cm_report_profiles_cache', JSON.stringify(mockProfiles));
      localStorage.setItem('cm_report_profiles_cache_ts', 'not-a-date');

      expect(profileCache.isValid()).toBe(false);
    });
  });

  describe('error handling', () => {
    it('should not throw when localStorage.setItem throws', () => {
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      expect(() => profileCache.save(mockProfiles)).not.toThrow();
    });

    it('should return null from load when localStorage.getItem throws', () => {
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('SecurityError');
      });

      expect(profileCache.load()).toBeNull();
    });
  });
});
