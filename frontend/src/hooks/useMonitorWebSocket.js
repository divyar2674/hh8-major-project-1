// Simplified WebSocket hook — tries to connect, gracefully handles failure
import { useState, useEffect, useRef } from 'react';

export default function useMonitorWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const retryRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const connect = () => {
      try {
        const wsBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
        const wsUrl = wsBase.replace(/^http/, 'ws') + '/monitor/ws';
        const ws = new WebSocket(`${wsUrl}?token=${token}`);
        wsRef.current = ws;

        ws.onopen = () => setConnected(true);
        ws.onmessage = (e) => {
          try { setLastEvent(JSON.parse(e.data)); } catch {}
        };
        ws.onclose = () => {
          setConnected(false);
          // Retry after 10 seconds if closed unexpectedly
          retryRef.current = setTimeout(connect, 10000);
        };
        ws.onerror = () => {
          ws.close();
        };
      } catch {
        // WebSocket not available, silently ignore
      }
    };

    connect();

    return () => {
      clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { connected, lastEvent };
}
