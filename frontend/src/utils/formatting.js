export function formatPriority(priority) {
  switch ((priority || "").toLowerCase()) {
    case "high":
      return { label: "HIGH PRIORITY", className: "priority-high", color: "#dc2626" };
    case "medium":
      return { label: "MEDIUM PRIORITY", className: "priority-medium", color: "#d97706" };
    case "low":
      return { label: "LOW PRIORITY", className: "priority-low", color: "#2563eb" };
    default:
      return { label: "UNKNOWN", className: "priority-unknown", color: "#4b5563" };
  }
}

export function formatTime(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    return isoString;
  }
}
