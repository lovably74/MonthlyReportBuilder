import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { SettingsPage } from './SettingsPage';
import { useProfileStore } from '../stores/profileStore';
import { useConnectionStore } from '../stores/connectionStore';

describe('SettingsPage', () => {
  beforeEach(() => {
    useProfileStore.setState({
      profiles: [],
      selectedProfileId: null,
      isLoading: false,
      error: null,
    });
    useConnectionStore.setState({
      status: 'connected',
      serverUrl: 'http://localhost:8741',
      serverId: 'test-id',
      lastPingAt: null,
    });
  });

  it('Settings 페이지를 렌더링한다', () => {
    render(<SettingsPage />);
    expect(screen.getByTestId('settings-page')).toBeInTheDocument();
    expect(screen.getByText('환경설정')).toBeInTheDocument();
  });

  it('프로필 탭을 표시한다', () => {
    render(<SettingsPage />);
    expect(screen.getByRole('tab', { name: '프로필' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '프로필' })).toHaveAttribute('aria-selected', 'true');
  });

  it('ProfileTab이 렌더링된다', () => {
    render(<SettingsPage />);
    expect(screen.getByTestId('profile-tab')).toBeInTheDocument();
  });

  it('ConnectionStatus가 헤더에 표시된다', () => {
    render(<SettingsPage />);
    expect(screen.getByLabelText(/서버 연결 상태/)).toBeInTheDocument();
  });

  it('서버 연결 끊김 시 DisconnectedBanner가 표시된다', () => {
    useConnectionStore.setState({ status: 'disconnected' });
    render(<SettingsPage />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/서버와 연결이 끊어졌습니다/)).toBeInTheDocument();
  });
});
