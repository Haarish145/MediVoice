import { useState, useEffect, useRef, useCallback } from "react";
import { createPatientWebSocket, createNurseWebSocket } from "../services/websocket";

const RECONNECT_DELAY_MS = 3000;

function buildWebSocket(role, sessionId, handlers) {
  if (role === "patient") return createPatientWebSocket(sessionId, handlers);
  return createNurseWebSocket(sessionId, handlers);
}

export function useWebSocket(role, sessionId) {
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!sessionId) return;

    const handlers = {
      onOpen: () => {
        if (!mountedRef.current) return;
        setConnectionStatus("connected");
      },
      onClose: () => {
        if (!mountedRef.current) return;
        setConnectionStatus("reconnecting");
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, RECONNECT_DELAY_MS);
      },
      onError: () => {
        if (!mountedRef.current) return;
        setConnectionStatus("error");
      },
      onMessage: (data) => {
        if (!mountedRef.current) return;
        setLastEvent(data);
      }
    };

    wsRef.current = buildWebSocket(role, sessionId, handlers);
  }, [role, sessionId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { connectionStatus, lastEvent, sendMessage };
}
