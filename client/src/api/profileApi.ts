import { useConnectionStore } from '../stores/connectionStore';
import type {
  Profile,
  ProfileCreateInput,
  ProfileUpdateInput,
  ProfileListResponse,
} from '../types/profile';

/**
 * API 에러 클래스
 * 서버가 HTTP 에러 응답(4xx, 5xx)을 반환했을 때 throw 된다.
 */
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    message: string,
    public field?: string | null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * 네트워크 에러 클래스
 * 서버와 연결이 끊어졌거나 fetch 요청 자체가 실패했을 때 throw 된다.
 */
export class NetworkError extends Error {
  constructor() {
    super('서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.');
    this.name = 'NetworkError';
  }
}

/**
 * 모든 API 요청에 포함할 공통 헤더를 반환한다.
 * X-Server-ID 헤더로 서버 인증 토큰을 전달한다.
 */
function getHeaders(): HeadersInit {
  const { serverId } = useConnectionStore.getState();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (serverId) {
    headers['X-Server-ID'] = serverId;
  }
  return headers;
}

/**
 * connectionStore에서 서버 기본 URL을 가져온다.
 */
function getBaseUrl(): string {
  const { serverUrl } = useConnectionStore.getState();
  return serverUrl ?? '';
}

/**
 * HTTP 에러 응답을 파싱하여 ApiError로 변환한다.
 */
async function handleErrorResponse(response: Response): Promise<never> {
  let errorCode = 'UNKNOWN_ERROR';
  let message = `HTTP ${response.status} 에러가 발생했습니다.`;
  let field: string | null = null;

  try {
    const body = await response.json();
    if (body.error_code) {
      errorCode = body.error_code;
    }
    if (body.message) {
      message = body.message;
    }
    if (body.field) {
      field = body.field;
    }
  } catch {
    // JSON 파싱 실패 시 기본 에러 메시지 사용
  }

  throw new ApiError(response.status, errorCode, message, field);
}

/**
 * fetch 래퍼 — 네트워크 오류를 NetworkError로 변환한다.
 */
async function request<T>(url: string, options: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch {
    throw new NetworkError();
  }

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  // DELETE는 응답 본문이 없을 수 있음
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ─── API 메서드 ────────────────────────────────────────────────────────────────

/**
 * 프로필 목록을 조회한다.
 */
export async function fetchProfiles(): Promise<ProfileListResponse> {
  const baseUrl = getBaseUrl();
  return request<ProfileListResponse>(`${baseUrl}/api/v1/profiles`, {
    method: 'GET',
    headers: getHeaders(),
  });
}

/**
 * 새 프로필을 생성한다.
 */
export async function createProfile(data: ProfileCreateInput): Promise<Profile> {
  const baseUrl = getBaseUrl();
  return request<Profile>(`${baseUrl}/api/v1/profiles`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * 기존 프로필을 수정한다.
 */
export async function updateProfile(id: number, data: ProfileUpdateInput): Promise<Profile> {
  const baseUrl = getBaseUrl();
  return request<Profile>(`${baseUrl}/api/v1/profiles/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
}

/**
 * 프로필을 삭제한다.
 */
export async function deleteProfile(id: number): Promise<void> {
  const baseUrl = getBaseUrl();
  return request<void>(`${baseUrl}/api/v1/profiles/${id}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
}

/**
 * 프로필을 복사한다.
 */
export async function copyProfile(id: number): Promise<Profile> {
  const baseUrl = getBaseUrl();
  return request<Profile>(`${baseUrl}/api/v1/profiles/${id}/copy`, {
    method: 'POST',
    headers: getHeaders(),
  });
}

/**
 * 프로필을 기본 프로필로 지정한다.
 */
export async function setDefaultProfile(id: number): Promise<Profile> {
  const baseUrl = getBaseUrl();
  return request<Profile>(`${baseUrl}/api/v1/profiles/${id}/default`, {
    method: 'PUT',
    headers: getHeaders(),
  });
}

/**
 * 프로필을 JSON으로 내보낸다.
 */
export async function exportProfile(id: number): Promise<object> {
  const baseUrl = getBaseUrl();
  return request<object>(`${baseUrl}/api/v1/profiles/${id}/export`, {
    method: 'GET',
    headers: getHeaders(),
  });
}

/**
 * JSON 데이터로 프로필을 가져온다.
 */
export async function importProfile(data: object): Promise<Profile> {
  const baseUrl = getBaseUrl();
  return request<Profile>(`${baseUrl}/api/v1/profiles/import`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
}
