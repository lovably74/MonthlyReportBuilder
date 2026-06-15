/**
 * 프로필 로컬 캐시 저장소
 *
 * localStorage 기반으로 프로필 목록을 캐시하여
 * 서버 연결 끊김 시 읽기 전용 조회를 지원한다.
 *
 * Requirements: 9.2, 9.5
 */
import type { Profile } from '../types/profile';

const CACHE_KEY = 'cm_report_profiles_cache';
const CACHE_TIMESTAMP_KEY = 'cm_report_profiles_cache_ts';

/** 캐시 유효 기간: 24시간 (ms) */
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

export const profileCache = {
  /**
   * 프로필 목록을 로컬 캐시에 저장한다.
   * API 응답 성공 시 호출하여 오프라인 대비용 캐시를 갱신한다.
   */
  save(profiles: Profile[]): void {
    try {
      const data = JSON.stringify(profiles);
      localStorage.setItem(CACHE_KEY, data);
      localStorage.setItem(CACHE_TIMESTAMP_KEY, new Date().toISOString());
    } catch {
      // localStorage 용량 초과 등 에러 시 무시 (캐시는 best-effort)
    }
  },

  /**
   * 캐시된 프로필 목록을 반환한다.
   * 캐시가 없거나 파싱 실패 시 null을 반환한다.
   */
  load(): Profile[] | null {
    try {
      const data = localStorage.getItem(CACHE_KEY);
      if (data === null) {
        return null;
      }
      const profiles: Profile[] = JSON.parse(data);
      if (!Array.isArray(profiles)) {
        return null;
      }
      return profiles;
    } catch {
      // JSON 파싱 에러 시 null 반환
      return null;
    }
  },

  /**
   * 마지막 캐시 저장 시각을 ISO 8601 문자열로 반환한다.
   * 캐시가 없으면 null을 반환한다.
   */
  getLastCachedAt(): string | null {
    return localStorage.getItem(CACHE_TIMESTAMP_KEY);
  },

  /**
   * 캐시를 삭제한다.
   */
  clear(): void {
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(CACHE_TIMESTAMP_KEY);
  },

  /**
   * 캐시가 존재하고 24시간 이내에 저장된 경우 true를 반환한다.
   */
  isValid(): boolean {
    const timestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY);
    if (timestamp === null) {
      return false;
    }
    try {
      const cachedAt = new Date(timestamp).getTime();
      if (isNaN(cachedAt)) {
        return false;
      }
      const now = Date.now();
      return now - cachedAt < CACHE_TTL_MS;
    } catch {
      return false;
    }
  },
};
