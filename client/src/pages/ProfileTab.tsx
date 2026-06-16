import { useState, useEffect, useCallback } from 'react';
import { useProfileStore } from '../stores/profileStore';
import { useIsDisconnected } from '../components/ConnectionStatus';
import { useToastStore } from '../stores/toastStore';
import { ProfileList } from '../components/ProfileList';
import { ProfileForm } from '../components/ProfileForm';
import { ProfileActions } from '../components/ProfileActions';
import { DeleteConfirmDialog } from '../components/DeleteConfirmDialog';
import { ImportDialog } from '../components/ImportDialog';
import { RetryableError } from '../components/RetryableError';

type ViewMode = 'list' | 'create' | 'edit';

/**
 * 프로필 관리 탭 컨테이너
 * ProfileList, ProfileForm, ProfileActions, DeleteConfirmDialog, ImportDialog를 조립하고
 * ProfileStore를 통한 데이터 플로우를 연결한다.
 *
 * Requirements: 8.1, 8.6
 */
export function ProfileTab() {
  const {
    profiles,
    selectedProfileId,
    error,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    copyProfile,
    exportProfile,
    importProfile,
    clearError,
  } = useProfileStore();

  const isDisconnected = useIsDisconnected();
  const showSuccess = useToastStore((state) => state.showSuccess);
  const showError = useToastStore((state) => state.showError);

  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; name: string } | null>(null);
  const [importConflict, setImportConflict] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  // 초기 프로필 목록 로드
  useEffect(() => {
    fetchProfiles().then(() => {
      const { error: currentError } = useProfileStore.getState();
      if (currentError) {
        setLoadFailed(true);
      }
    });
  }, [fetchProfiles]);

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId) ?? null;

  const handleCreate = useCallback(async (data: { name: string; description: string }) => {
    await createProfile({ name: data.name, description: data.description });
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필이 생성되었습니다.');
      setViewMode('list');
    } else {
      showError(currentError);
    }
  }, [createProfile, showSuccess, showError]);

  const handleUpdate = useCallback(async (data: { name: string; description: string }) => {
    if (!selectedProfileId) return;
    await updateProfile(selectedProfileId, { name: data.name, description: data.description });
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필이 수정되었습니다.');
      setViewMode('list');
    } else {
      showError(currentError);
    }
  }, [selectedProfileId, updateProfile, showSuccess, showError]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    await deleteProfile(deleteTarget.id);
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필이 삭제되었습니다.');
    } else {
      showError(currentError);
    }
    setDeleteTarget(null);
  }, [deleteTarget, deleteProfile, showSuccess, showError]);

  const handleCopy = useCallback(async (id: number) => {
    await copyProfile(id);
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필이 복사되었습니다.');
    } else {
      showError(currentError);
    }
  }, [copyProfile, showSuccess, showError]);

  const handleExport = useCallback(async (id: number) => {
    await exportProfile(id);
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필이 내보내기되었습니다.');
    } else {
      showError(currentError);
    }
  }, [exportProfile, showSuccess, showError]);

  const handleImport = useCallback(async (data: object) => {
    await importProfile(data);
    const { error: currentError } = useProfileStore.getState();
    if (!currentError) {
      showSuccess('프로필을 가져왔습니다.');
      setImportConflict(null);
    } else {
      showError(currentError);
    }
  }, [importProfile, showSuccess, showError]);

  const handleRetry = useCallback(() => {
    setLoadFailed(false);
    clearError();
    fetchProfiles();
  }, [clearError, fetchProfiles]);

  // 목록 로드 실패 시 재시도 가능한 에러 표시
  if (loadFailed && error) {
    return (
      <div className="profile-tab" data-testid="profile-tab">
        <RetryableError message={error} onRetry={handleRetry} />
      </div>
    );
  }

  return (
    <div className="profile-tab" data-testid="profile-tab">
      {/* 생성 버튼 (목록 뷰에서만) */}
      {viewMode === 'list' && (
        <div className="profile-tab__header">
          <button
            type="button"
            className="profile-tab__create-btn"
            onClick={() => setViewMode('create')}
            disabled={isDisconnected}
            data-testid="profile-create-button"
          >
            새 프로필
          </button>
        </div>
      )}

      {/* 프로필 목록 */}
      {viewMode === 'list' && (
        <>
          <ProfileList onCreate={() => setViewMode('create')} />

          {/* 선택된 프로필의 액션 버튼 */}
          {selectedProfile && (
            <ProfileActions
              profileId={selectedProfile.id}
              profileName={selectedProfile.name}
              isDisabled={isDisconnected}
              onCopy={handleCopy}
              onExport={handleExport}
              onDelete={(id, name) => setDeleteTarget({ id, name })}
            />
          )}
        </>
      )}

      {/* 프로필 생성 폼 */}
      {viewMode === 'create' && (
        <ProfileForm
          mode="create"
          onSubmit={handleCreate}
          onCancel={() => setViewMode('list')}
        />
      )}

      {/* 프로필 수정 폼 */}
      {viewMode === 'edit' && selectedProfile && (
        <ProfileForm
          mode="edit"
          initialValues={{
            name: selectedProfile.name,
            description: selectedProfile.description,
          }}
          onSubmit={handleUpdate}
          onCancel={() => setViewMode('list')}
        />
      )}

      {/* 삭제 확인 대화상자 */}
      <DeleteConfirmDialog
        isOpen={deleteTarget !== null}
        profileName={deleteTarget?.name ?? ''}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* 가져오기 이름 충돌 대화상자 */}
      <ImportDialog
        isOpen={importConflict !== null}
        conflictName={importConflict ?? ''}
        onNewName={(name) => {
          handleImport({ name });
          setImportConflict(null);
        }}
        onCancel={() => setImportConflict(null)}
      />
    </div>
  );
}

export default ProfileTab;
