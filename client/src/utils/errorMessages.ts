/**
 * 서버 에러 코드 → 한국어 사용자 메시지 매핑
 * 서버 API에서 반환하는 error_code를 사용자에게 표시할 한국어 메시지로 변환한다.
 */
export const ERROR_MESSAGES: Record<string, string> = {
  PROFILE_NAME_REQUIRED: '프로필명은 필수 입력값입니다.',
  PROFILE_NAME_TOO_LONG: '프로필명은 50자를 초과할 수 없습니다.',
  PROFILE_DESC_TOO_LONG: '설명은 200자를 초과할 수 없습니다.',
  PROFILE_NAME_DUPLICATE: '동일한 이름의 프로필이 이미 존재합니다.',
  PROFILE_NOT_FOUND: '해당 프로필을 찾을 수 없습니다.',
  PROFILE_LAST_DELETE: '최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다.',
  IMPORT_INVALID_JSON: '유효하지 않은 JSON 파일입니다.',
  IMPORT_MISSING_FIELD: '필수 항목(프로필명)이 누락되었습니다.',
  IMPORT_FILE_TOO_LARGE: '파일 크기가 10MB를 초과합니다.',
  DATABASE_ERROR: '데이터베이스 접근에 실패했습니다. 앱을 재시작해 주세요.',
  NETWORK_ERROR: '서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.',
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다.',
};

/**
 * 에러 코드에 해당하는 한국어 메시지를 반환한다.
 * 알 수 없는 에러 코드의 경우 기본 메시지를 반환한다.
 */
export function getErrorMessage(errorCode: string): string {
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.UNKNOWN_ERROR;
}
