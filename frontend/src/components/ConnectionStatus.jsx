export default function ConnectionStatus({ status }) {
  const label = {
    connected: "Connected",
    reconnecting: "Reconnecting...",
    disconnected: "Disconnected",
    error: "Connection Error"
  }[status] || status;

  const cls = {
    connected: "status-connected",
    reconnecting: "status-reconnecting",
    disconnected: "status-disconnected",
    error: "status-disconnected"
  }[status] || "status-disconnected";

  return (
    <span className={`status-pill ${cls}`} aria-live="polite">
      <span className="status-dot" />
      {label}
    </span>
  );
}
