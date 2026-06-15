/**
 * 프로필 상태 관리 Zustand Store
 *
 * 서버 연결 상태에 따라 API 호출 또는 로컬 캐시 fallback을 수행한다.
 * 쓰기 작업(생성, 수정, 삭제, 복사, 기본 지정, 가져오기)은
 * 서버 연결이 끊어진 상태에서 차단된다.
 *
 * Requirements: 9.2, 9.3, 9.5
 */
import { create } from 'zustand';
import type { Profile, ProfileCreateInput, ProfileUpdateInput } from '../types/profile';
import * as api from '../api/profileApi';
import { ApiError, NetworkError } from '../api/profileApi';
import { profileCache } from '../cache/profileCache';
import { useConnectionStore } from './connectionStore';

/** 서버 연결 끊김 시 표시할 에러 메시지 */
const DISCONNECTED_ERROR_MESSAGE =
  '서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.';

export interface ProfileStore {
  profiles: Profile[];
  selectedProfileId: number | null;
  isLoading: boolean;
  error: string | null;

  fetchProfiles: () => Promise<void>;
  createProfile: (data: ProfileCreateInput) => Promise<void>;
  updateProfile: (id: number, data: ProfileUpdateInput) => Promise<void>;
  deleteProfile: (id: number) => Promise<void>;
  copyProfile: (id: number) => Promise<void>;
  setDefaultProfile: (id: number) => Promise<void>;
  exportProfile: (id: number) => Promise<object>;
  importProfile: (data: object) => Promise<void>;
  selectProfile: (id: number | null) => void;
  clearError: () => void;
}

/**
 * 서버 연결 여부를 확인한다.
 */
function isConnected(): boolean {
  const { status } = useConnectionStore.getState();
  return status === 'connected';
}

/**
 * 에러 객체에서 사용자에게 표시할 메시지를 추출한다.
 */
function extractErrorMessage(error: unknown): string {
  if (error instanceof NetworkError) {
    return error.message;
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '알 수 없는 오류가 발생했습니다.';
}

export const useProfileStore = create<ProfileStore>((set, get) => ({
  profiles: [],
  selectedProfileId: null,
  isLoading: false,
  error: null,

  /**
   * 프로필 목록을 조회한다.
   * - 서버 연결 시: API 호출 후 캐시 갱신
   * - 서버 미연결 시: 로컬 캐시에서 읽기 전용 로드
   */
  fetchProfiles: async () => {
    set({ isLoading: true, error: null });

    try {
      if (isConnected()) {
        const response = await api.fetchProfiles();
        const profiles = response.profiles;
        set({ profiles, isLoading: false });
        profileCache.save(profiles);
      } else {
        // 서버 미연결: 캐시에서 로드
        const cached = profileCache.load();
        if (cached !== null) {
          set({ profiles: cached, isLoading: false });
        } else {
          set({ profiles: [], isLoading: false });
        }
      }
    } catch (error: unknown) {
      const message = extractErrorMessage(error);
      // 네트워크 에러 발생 시 캐시 fallback 시도
      if (error instanceof NetworkError) {
        const cached = profileCache.load();
        if (cached !== null) {
          set({ profiles: cached, isLoading: false, error: message });
        } else {
          set({ isLoading: false, error: message });
        }
      } else {
        set({ isLoading: false, error: message });
      }
    }
  },

  /**
   * 새 프로필을 생성한다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  createProfile: async (data: ProfileCreateInput) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.createProfile(data);
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 기존 프로필을 수정한다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  updateProfile: async (id: number, data: ProfileUpdateInput) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.updateProfile(id, data);
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 프로필을 삭제한다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  deleteProfile: async (id: number) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.deleteProfile(id);
      // 삭제된 프로필이 선택 상태였으면 선택 해제
      if (get().selectedProfileId === id) {
        set({ selectedProfileId: null });
      }
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 프로필을 복사한다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  copyProfile: async (id: number) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.copyProfile(id);
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 프로필을 기본 프로필로 지정한다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  setDefaultProfile: async (id: number) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.setDefaultProfile(id);
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 프로필을 JSON으로 내보낸다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  exportProfile: async (id: number) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return {};
    }

    set({ error: null });
    try {
      const data = await api.exportProfile(id);
      return data;
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
      return {};
    }
  },

  /**
   * JSON 데이터로 프로필을 가져온다.
   * 서버 미연결 시 에러 메시지를 설정하고 작업을 차단한다.
   */
  importProfile: async (data: object) => {
    if (!isConnected()) {
      set({ error: DISCONNECTED_ERROR_MESSAGE });
      return;
    }

    set({ error: null });
    try {
      await api.importProfile(data);
      await get().fetchProfiles();
    } catch (error: unknown) {
      set({ error: extractErrorMessage(error) });
    }
  },

  /**
   * 프로필을 선택한다.
   */
  selectProfile: (id: number | null) => {
    set({ selectedProfileId: id });
  },

  /**
   * 에러 상태를 초기화한다.
   */
  clearError: () => {
    set({ error: null });
  },
}));
