import { describe, it, expect } from 'vitest';
import { getErrorMessage, ERROR_MESSAGES } from '@/utils/errorMessages';

describe('errorMessages', () => {
  describe('getErrorMessage', () => {
    it('should return correct message for PROFILE_NAME_REQUIRED', () => {
      expect(getErrorMessage('PROFILE_NAME_REQUIRED')).toBe('프로필명은 필수 입력값입니다.');
    });

    it('should return correct message for PROFILE_NAME_TOO_LONG', () => {
      expect(getErrorMessage('PROFILE_NAME_TOO_LONG')).toBe('프로필명은 50자를 초과할 수 없습니다.');
    });

    it('should return correct message for PROFILE_NAME_DUPLICATE', () => {
      expect(getErrorMessage('PROFILE_NAME_DUPLICATE')).toBe('동일한 이름의 프로필이 이미 존재합니다.');
    });

    it('should return correct message for PROFILE_NOT_FOUND', () => {
      expect(getErrorMessage('PROFILE_NOT_FOUND')).toBe('해당 프로필을 찾을 수 없습니다.');
    });

    it('should return correct message for PROFILE_LAST_DELETE', () => {
      expect(getErrorMessage('PROFILE_LAST_DELETE')).toBe(
        '최소 1개의 프로필이 필요합니다. 마지막 프로필은 삭제할 수 없습니다.',
      );
    });

    it('should return correct message for IMPORT_INVALID_JSON', () => {
      expect(getErrorMessage('IMPORT_INVALID_JSON')).toBe('유효하지 않은 JSON 파일입니다.');
    });

    it('should return correct message for IMPORT_MISSING_FIELD', () => {
      expect(getErrorMessage('IMPORT_MISSING_FIELD')).toBe('필수 항목(프로필명)이 누락되었습니다.');
    });

    it('should return correct message for IMPORT_FILE_TOO_LARGE', () => {
      expect(getErrorMessage('IMPORT_FILE_TOO_LARGE')).toBe('파일 크기가 10MB를 초과합니다.');
    });

    it('should return correct message for DATABASE_ERROR', () => {
      expect(getErrorMessage('DATABASE_ERROR')).toBe(
        '데이터베이스 접근에 실패했습니다. 앱을 재시작해 주세요.',
      );
    });

    it('should return correct message for NETWORK_ERROR', () => {
      expect(getErrorMessage('NETWORK_ERROR')).toBe(
        '서버와 연결이 끊어졌습니다. 서버 연결 상태를 확인해 주세요.',
      );
    });

    it('should return fallback message for unknown error codes', () => {
      expect(getErrorMessage('SOME_UNKNOWN_CODE')).toBe('알 수 없는 오류가 발생했습니다.');
    });

    it('should return fallback message for empty string code', () => {
      expect(getErrorMessage('')).toBe('알 수 없는 오류가 발생했습니다.');
    });
  });

  describe('ERROR_MESSAGES constant', () => {
    it('should contain all expected error codes', () => {
      const expectedCodes = [
        'PROFILE_NAME_REQUIRED',
        'PROFILE_NAME_TOO_LONG',
        'PROFILE_DESC_TOO_LONG',
        'PROFILE_NAME_DUPLICATE',
        'PROFILE_NOT_FOUND',
        'PROFILE_LAST_DELETE',
        'IMPORT_INVALID_JSON',
        'IMPORT_MISSING_FIELD',
        'IMPORT_FILE_TOO_LARGE',
        'DATABASE_ERROR',
        'NETWORK_ERROR',
        'UNKNOWN_ERROR',
      ];

      for (const code of expectedCodes) {
        expect(ERROR_MESSAGES).toHaveProperty(code);
        expect(typeof ERROR_MESSAGES[code]).toBe('string');
        expect(ERROR_MESSAGES[code].length).toBeGreaterThan(0);
      }
    });
  });
});
