import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useConnectionStore, CONNECTION_RESTORED_EVENT } from '@/stores/connectionStore';

describe('connectionStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const store = useConnectionStore.getState();
    store.stopHealthCheck();
    useConnectionStore.setState({
      status: 'disconnected',
      serverUrl: null,
      serverId: null,
      lastPingAt: null,
    });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    useConnectionStore.getState().stopHealthCheck();
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should have status "disconnected" initially', () => {
      const { status } = useConnectionStore.getState();
      expect(status).toBe('disconnected');
    });

    it('should have null serverUrl initially', () => {
      const { serverUrl } = useConnectionStore.getState();
      expect(serverUrl).toBeNull();
    });

    it('should have null serverId initially', () => {
      const { serverId } = useConnectionStore.getState();
      expect(serverId).toBeNull();
    });

    it('should have null lastPingAt initially', () => {
      const { lastPingAt } = useConnectionStore.getState();
      expect(lastPingAt).toBeNull();
    });
  });

  describe('setServerInfo', () => {
    it('should update serverUrl and serverId', () => {
      const store = useConnectionStore.getState();
      store.setServerInfo('http://192.168.1.10:8741', 'abc-123-uuid');

      const { serverUrl, serverId } = useConnectionStore.getState();
      expect(serverUrl).toBe('http://192.168.1.10:8741');
      expect(serverId).toBe('abc-123-uuid');
    });

    it('should not change status when setting server info', () => {
      const store = useConnectionStore.getState();
      store.setServerInfo('http://192.168.1.10:8741', 'abc-123-uuid');

      const { status } = useConnectionStore.getState();
      expect(status).toBe('disconnected');
    });
  });

  describe('ping', () => {
    it('should return false and stay disconnected if serverUrl is null', async () => {
      const store = useConnectionStore.getState();
      const result = await store.ping();

      expect(result).toBe(false);
      expect(useConnectionStore.getState().status).toBe('disconnected');
    });

    it('should transition to connected on successful ping', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
      }));

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');

      const result = await store.ping();

      expect(result).toBe(true);
      expect(useConnectionStore.getState().status).toBe('connected');
      expect(useConnectionStore.getState().lastPingAt).not.toBeNull();
    });

    it('should call GET /health on the server URL', async () => {
      const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
      vi.stubGlobal('fetch', mockFetch);

      const store = useConnectionStore.getState();
      store.setServerInfo('http://192.168.1.5:8741', 'server-id-2');

      await store.ping();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://192.168.1.5:8741/health',
        expect.objectContaining({ method: 'GET' }),
      );
    });

    it('should transition to disconnected on fetch failure (network error)', async () => {
      vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')));

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');

      // First set to connected
      useConnectionStore.setState({ status: 'connected' });

      const result = await store.ping();

      expect(result).toBe(false);
      expect(useConnectionStore.getState().status).toBe('disconnected');
    });

    it('should transition to disconnected on non-ok response', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      }));

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');
      useConnectionStore.setState({ status: 'connected' });

      const result = await store.ping();

      expect(result).toBe(false);
      expect(useConnectionStore.getState().status).toBe('disconnected');
    });

    it('should dispatch CONNECTION_RESTORED_EVENT when reconnecting', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200 }));

      const eventHandler = vi.fn();
      window.addEventListener(CONNECTION_RESTORED_EVENT, eventHandler);

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');
      // status starts as disconnected, so ping success should trigger event
      await store.ping();

      expect(eventHandler).toHaveBeenCalledTimes(1);

      window.removeEventListener(CONNECTION_RESTORED_EVENT, eventHandler);
    });

    it('should NOT dispatch CONNECTION_RESTORED_EVENT when already connected', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200 }));

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');

      // First ping to get connected
      await store.ping();

      const eventHandler = vi.fn();
      window.addEventListener(CONNECTION_RESTORED_EVENT, eventHandler);

      // Second ping while already connected
      await store.ping();

      expect(eventHandler).not.toHaveBeenCalled();

      window.removeEventListener(CONNECTION_RESTORED_EVENT, eventHandler);
    });

    it('should set status to connecting when pinging from disconnected state', async () => {
      let statusDuringFetch: string | null = null;

      vi.stubGlobal('fetch', vi.fn().mockImplementation(() => {
        statusDuringFetch = useConnectionStore.getState().status;
        return Promise.resolve({ ok: true, status: 200 });
      }));

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');

      await store.ping();

      expect(statusDuringFetch).toBe('connecting');
    });
  });

  describe('startHealthCheck / stopHealthCheck', () => {
    it('should start periodic pings', async () => {
      vi.useFakeTimers();
      const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
      vi.stubGlobal('fetch', mockFetch);

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');
      store.startHealthCheck();

      // Initial ping called immediately
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Advance 5 seconds
      await vi.advanceTimersByTimeAsync(5000);
      expect(mockFetch).toHaveBeenCalledTimes(2);

      // Advance another 5 seconds
      await vi.advanceTimersByTimeAsync(5000);
      expect(mockFetch).toHaveBeenCalledTimes(3);

      store.stopHealthCheck();
    });

    it('should stop periodic pings when stopHealthCheck is called', async () => {
      vi.useFakeTimers();
      const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
      vi.stubGlobal('fetch', mockFetch);

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');
      store.startHealthCheck();

      // Initial ping
      expect(mockFetch).toHaveBeenCalledTimes(1);

      store.stopHealthCheck();

      // Advance time — no more pings should occur
      await vi.advanceTimersByTimeAsync(15000);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should prevent duplicate intervals when startHealthCheck called multiple times', async () => {
      vi.useFakeTimers();
      const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
      vi.stubGlobal('fetch', mockFetch);

      const store = useConnectionStore.getState();
      store.setServerInfo('http://localhost:8741', 'server-id-1');

      // Start multiple times
      store.startHealthCheck();
      store.startHealthCheck();
      store.startHealthCheck();

      // Should only have initial pings (3 calls to start = 3 immediate pings)
      expect(mockFetch).toHaveBeenCalledTimes(3);

      // But only 1 interval should be active
      await vi.advanceTimersByTimeAsync(5000);
      // 3 initial + 1 interval tick = 4
      expect(mockFetch).toHaveBeenCalledTimes(4);

      store.stopHealthCheck();
    });
  });
});
