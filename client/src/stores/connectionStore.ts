import { create } from 'zustand';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface ConnectionStore {
  status: ConnectionStatus;
  serverUrl: string | null;
  serverId: string | null;
  lastPingAt: string | null;

  // Actions
  setServerInfo: (url: string, serverId: string) => void;
  startHealthCheck: () => void;
  stopHealthCheck: () => void;
  ping: () => Promise<boolean>;
}

/** Event name emitted when connection is restored (disconnected → connected) */
export const CONNECTION_RESTORED_EVENT = 'connection:restored';

let healthCheckIntervalId: ReturnType<typeof setInterval> | null = null;

export const useConnectionStore = create<ConnectionStore>((set, get) => ({
  status: 'disconnected',
  serverUrl: null,
  serverId: null,
  lastPingAt: null,

  setServerInfo: (url: string, serverId: string) => {
    set({ serverUrl: url, serverId });
  },

  startHealthCheck: () => {
    // Prevent duplicate intervals
    if (healthCheckIntervalId !== null) {
      clearInterval(healthCheckIntervalId);
    }

    // Run an initial ping immediately
    get().ping();

    // Schedule periodic health checks every 5 seconds
    healthCheckIntervalId = setInterval(() => {
      get().ping();
    }, 5000);
  },

  stopHealthCheck: () => {
    if (healthCheckIntervalId !== null) {
      clearInterval(healthCheckIntervalId);
      healthCheckIntervalId = null;
    }
  },

  ping: async () => {
    const { serverUrl, status: previousStatus } = get();

    if (!serverUrl) {
      set({ status: 'disconnected' });
      return false;
    }

    // Transition to 'connecting' only if currently disconnected
    if (previousStatus === 'disconnected') {
      set({ status: 'connecting' });
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const response = await fetch(`${serverUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const now = new Date().toISOString();
        const wasDisconnected = get().status !== 'connected' || previousStatus === 'disconnected' || previousStatus === 'connecting';

        set({ status: 'connected', lastPingAt: now });

        // Emit reconnection event when transitioning from disconnected/connecting to connected
        if (wasDisconnected) {
          window.dispatchEvent(new CustomEvent(CONNECTION_RESTORED_EVENT));
        }

        return true;
      } else {
        set({ status: 'disconnected' });
        return false;
      }
    } catch {
      set({ status: 'disconnected' });
      return false;
    }
  },
}));
