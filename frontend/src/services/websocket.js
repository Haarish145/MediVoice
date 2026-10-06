function getBaseWsUrl() {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL.replace(/\/+$/, "");
  }
  if (import.meta.env.VITE_BACKEND_URL) {
    const backend = import.meta.env.VITE_BACKEND_URL.replace(/\/+$/, "");
    return backend.replace(/^http:\/\//i, "ws://").replace(/^https:\/\//i, "wss://");
  }
  return "ws://localhost:8000";
}

const BASE_WS_URL = getBaseWsUrl();

export function createPatientWebSocket(sessionId, handlers = {}) {
  const ws = new WebSocket(`${BASE_WS_URL}/ws/patient/${sessionId}`);

  ws.onopen = () => handlers.onOpen?.();
  ws.onclose = (e) => handlers.onClose?.(e);
  ws.onerror = (e) => handlers.onError?.(e);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onMessage?.(data);
    } catch (err) {
      console.error("Failed to parse patient WS message:", err);
    }
  };

  return ws;
}

export function createNurseWebSocket(sessionId, handlers = {}) {
  const ws = new WebSocket(`${BASE_WS_URL}/ws/nurse/${sessionId}`);

  ws.onopen = () => handlers.onOpen?.();
  ws.onclose = (e) => handlers.onClose?.(e);
  ws.onerror = (e) => handlers.onError?.(e);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onMessage?.(data);
    } catch (err) {
      console.error("Failed to parse nurse WS message:", err);
    }
  };

  return ws;
}
