const rawBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const BASE_URL = rawBaseUrl.replace(/\/+$/, "");

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/api/health`);
  return res.json();
}

export async function fetchLanguages() {
  const res = await fetch(`${BASE_URL}/api/languages`);
  return res.json();
}

export async function createSession(language = "ta", patientName = "", facility = "") {
  const res = await fetch(`${BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      language,
      patient_name: patientName.trim() || "Anonymous Patient",
      facility: facility.trim() || "Emergency Triage Unit"
    })
  });
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${BASE_URL}/api/sessions`);
  return res.json();
}

export async function fetchSessionDetails(sessionId) {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}`);
  return res.json();
}

export async function markSessionSeen(sessionId, nurseUsername = "nurse_admin") {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}/seen`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nurse_username: nurseUsername })
  });
  return res.json();
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}`, {
    method: "DELETE"
  });
  return res.json();
}

export async function nurseLogin(username, password) {
  const res = await fetch(`${BASE_URL}/api/auth/nurse/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) {
    throw new Error("Invalid credentials");
  }
  return res.json();
}
