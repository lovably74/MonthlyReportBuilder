/**
 * 환경설정 프로필 데이터 모델
 * 서버 API 응답 및 클라이언트 상태에서 사용되는 TypeScript 인터페이스 정의
 */

/** 프로필 엔티티 (서버 응답) */
export interface Profile {
  id: number;
  name: string;
  description: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/** 프로필 생성 입력 */
export interface ProfileCreateInput {
  name: string;
  description?: string;
}

/** 프로필 수정 입력 */
export interface ProfileUpdateInput {
  name?: string;
  description?: string;
}

/** 프로필 목록 조회 응답 */
export interface ProfileListResponse {
  profiles: Profile[];
  total: number;
}
