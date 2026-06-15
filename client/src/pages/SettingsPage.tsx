import { useState } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { DisconnectedBanner } from '../components/DisconnectedBanner';
import { ConnectionStatus } from '../components/ConnectionStatus';
import { ToastContainer } from '../components/ToastContainer';
import { ProfileTab } from './ProfileTab';

type TabId = 'profile';

interface TabConfig {
  id: TabId;
  label: string;
}

const TABS: TabConfig[] = [
  { id: 'profile', label: '프로필' },
];

/**
 * 환경설정 메인 페이지 (탭 구조)
 * 첫 번째 탭: 프로필 관리 (ProfileTab)
 * DisconnectedBanner, ConnectionStatus, ToastContainer를 통합한다.
 *
 * Requirements: 8.1, 8.6
 */
export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('profile');

  return (
    <ErrorBoundary>
      <div className="settings-page" data-testid="settings-page">
        {/* 서버 연결 끊김 경고 배너 */}
        <DisconnectedBanner />

        {/* 페이지 헤더 */}
        <header className="settings-page__header">
          <h1 className="settings-page__title">환경설정</h1>
          <ConnectionStatus />
        </header>

        {/* 탭 네비게이션 */}
        <nav className="settings-page__tabs" role="tablist" aria-label="환경설정 탭">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              type="button"
              className={`settings-page__tab ${activeTab === tab.id ? 'settings-page__tab--active' : ''}`}
              aria-selected={activeTab === tab.id}
              aria-controls={`tabpanel-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* 탭 컨텐츠 */}
        <div
          className="settings-page__content"
          role="tabpanel"
          id={`tabpanel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
        >
          {activeTab === 'profile' && <ProfileTab />}
        </div>

        {/* 토스트 알림 */}
        <ToastContainer />
      </div>
    </ErrorBoundary>
  );
}

export default SettingsPage;
