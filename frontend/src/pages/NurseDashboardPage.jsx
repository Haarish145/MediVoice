import { useState, useEffect, useCallback } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { fetchSessions, markSessionSeen, deleteSession } from "../services/api";
import ConnectionStatus from "../components/ConnectionStatus";
import RedFlagAlert from "../components/RedFlagAlert";
import TriageStatus from "../components/TriageStatus";
import SummaryPanel from "../components/SummaryPanel";
import ConversationView from "../components/ConversationView";
import { formatPriority, formatTime } from "../utils/formatting";
import { SUPPORTED_LANGUAGES } from "../utils/languages";

function formatSeenTime(timestamp) {
  if (!timestamp) return null;
  try {
    const diffMs = Date.now() - new Date(timestamp).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return "just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    return formatTime(timestamp);
  } catch (e) {
    return "recently";
  }
}

function SessionCard({ sessionData, onClick, isActive }) {
  const ts = sessionData.triage_state || {};
  const { label, color } = formatPriority(ts.priority || sessionData.priority);
  const pName = sessionData.patient_name || ts.patient_name || "Anonymous Patient";
  const facility = sessionData.facility || ts.facility || "Emergency Triage Unit";
  const seenAt = sessionData.seen_at || ts.seen_at;
  const isCompleted = sessionData.is_completed || ts.is_completed || sessionData.status === "completed";

  return (
    <div
      onClick={onClick}
      style={{
        padding: "0.85rem",
        border: `2px solid ${isActive ? "#005691" : "#e5e7eb"}`,
        borderRadius: "8px",
        cursor: "pointer",
        background: isActive ? "#e6f0fa" : "white",
        marginBottom: "0.6rem",
        transition: "all 0.15s",
        boxShadow: isActive ? "0 2px 6px rgba(0,86,145,0.15)" : "none",
        position: "relative"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontWeight: "700", fontSize: "0.95rem", color: "#005691" }}>
            👤 {pName}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.15rem" }}>
            {sessionData.session_id} &bull; {SUPPORTED_LANGUAGES.find(l => l.language_code === sessionData.language)?.display_name || sessionData.language}
          </div>
          <div style={{ fontSize: "0.72rem", color: "#0369a1", marginTop: "0.1rem" }}>
            🏥 {facility}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.25rem" }}>
          <span style={{
            fontSize: "0.72rem", padding: "0.15rem 0.5rem", borderRadius: "12px",
            background: color + "22", color, fontWeight: "700", border: `1px solid ${color}`
          }}>
            {label}
          </span>
          {isCompleted && (
            <span style={{
              fontSize: "0.68rem", padding: "0.1rem 0.4rem", borderRadius: "10px",
              background: "#dcfce7", color: "#166534", fontWeight: "600", border: "1px solid #bbf7d0"
            }}>
              ✓ Complete
            </span>
          )}
        </div>
      </div>

      {(ts.main_complaint || sessionData.main_complaint) && (
        <div style={{ marginTop: "0.35rem", fontSize: "0.82rem", color: "#374151" }}>
          Complaint: <strong>{ts.main_complaint || sessionData.main_complaint}</strong>
        </div>
      )}

      {(ts.red_flags || sessionData.red_flags || []).length > 0 && (
        <div style={{ marginTop: "0.25rem", fontSize: "0.75rem", color: "#dc2626", fontWeight: "600" }}>
          ⚠ Red flag detected
        </div>
      )}

      {/* Seen / Unseen Status Indicator */}
      <div style={{ marginTop: "0.45rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        {seenAt ? (
          <span style={{ fontSize: "0.72rem", color: "#16a34a", fontWeight: "600", display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span>✓</span> Seen {formatSeenTime(seenAt)}
          </span>
        ) : (
          <span style={{
            fontSize: "0.7rem", color: "#b45309", background: "#fef3c7",
            padding: "0.1rem 0.45rem", borderRadius: "8px", fontWeight: "700"
          }}>
            🔔 New (Unseen)
          </span>
        )}
      </div>
    </div>
  );
}

export default function NurseDashboardPage({ nurseInfo, onLogout }) {
  const [sessions, setSessions] = useState({});
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [liveData, setLiveData] = useState({});
  const [isDeleting, setIsDeleting] = useState(false);

  // Load existing sessions from REST API
  const loadSessions = useCallback(async () => {
    try {
      const res = await fetchSessions();
      const map = {};
      const sessionList = res.sessions || [];
      for (const s of sessionList) {
        map[s.session_id] = s;
      }
      setSessions(map);
      
      // Auto-select latest session if none currently selected
      if (!activeSessionId && sessionList.length > 0) {
        const firstSid = sessionList[0].session_id;
        setActiveSessionId(firstSid);
        // Mark as seen automatically
        markSessionSeen(firstSid, nurseInfo?.username).catch(() => {});
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  }, [activeSessionId, nurseInfo]);

  useEffect(() => {
    loadSessions();
    const interval = setInterval(loadSessions, 5000);
    return () => clearInterval(interval);
  }, [loadSessions]);

  // When nurse switches active session, mark as seen
  const handleSelectSession = (sid) => {
    setActiveSessionId(sid);
    const s = liveData[sid] || sessions[sid];
    if (!s?.seen_at) {
      markSessionSeen(sid, nurseInfo?.username).then(res => {
        if (res?.seen_at) {
          setLiveData(prev => ({
            ...prev,
            [sid]: {
              ...(prev[sid] || sessions[sid] || {}),
              seen_at: res.seen_at,
              seen_by: res.seen_by
            }
          }));
          setSessions(prev => ({
            ...prev,
            [sid]: {
              ...(prev[sid] || {}),
              seen_at: res.seen_at,
              seen_by: res.seen_by
            }
          }));
        }
      }).catch(() => {});
    }
  };

  // Delete active session
  const handleDeleteSession = async () => {
    if (!activeSessionId) return;
    const confirmed = window.confirm(`Are you sure you want to permanently delete patient history for ${activeSessionId}?`);
    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await deleteSession(activeSessionId);
      
      // Remove from local states
      const remainingSids = Object.keys(sessions).filter(id => id !== activeSessionId);
      const newSessions = { ...sessions };
      delete newSessions[activeSessionId];
      setSessions(newSessions);

      const newLiveData = { ...liveData };
      delete newLiveData[activeSessionId];
      setLiveData(newLiveData);

      setActiveSessionId(remainingSids.length > 0 ? remainingSids[0] : null);
    } catch (err) {
      alert("Failed to delete session: " + err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  // Live WebSocket for active session
  const { connectionStatus, lastEvent } = useWebSocket(
    "nurse",
    activeSessionId
  );

  // Handle incoming real-time events from backend
  useEffect(() => {
    if (!lastEvent || !activeSessionId) return;
    const { event, session_id, data } = lastEvent;

    if (event === "nurse_dashboard_update" && session_id === activeSessionId) {
      setLiveData(prev => ({
        ...prev,
        [session_id]: data
      }));
    }
    if (event === "red_flag_detected" && session_id === activeSessionId) {
      setLiveData(prev => {
        const existing = prev[session_id] || {};
        return {
          ...prev,
          [session_id]: {
            ...existing,
            triage_state: {
              ...(existing.triage_state || {}),
              red_flags: data.red_flags || [],
              priority: "high"
            }
          }
        };
      });
    }
    if (event === "session_seen" && session_id) {
      setSessions(prev => ({
        ...prev,
        [session_id]: {
          ...(prev[session_id] || {}),
          seen_at: data.seen_at,
          seen_by: data.seen_by
        }
      }));
    }
    if (event === "session_deleted") {
      const delId = data.session_id;
      setSessions(prev => {
        const copy = { ...prev };
        delete copy[delId];
        return copy;
      });
      if (activeSessionId === delId) {
        setActiveSessionId(null);
      }
    }
    if (event === "connection") {
      const snapshot = data?.session_snapshot;
      if (snapshot && session_id === activeSessionId) {
        setLiveData(prev => ({ ...prev, [session_id]: snapshot }));
      }
    }
  }, [lastEvent, activeSessionId]);

  const sessionIds = Object.keys(sessions);
  const activeData = liveData[activeSessionId] || sessions[activeSessionId] || {};
  const activeTriageState = activeData?.triage_state || {};
  const activeMessages = activeData?.messages || [];
  const activePatientName = activeData?.patient_name || activeTriageState?.patient_name || "Anonymous Patient";
  const activeFacility = activeData?.facility || activeTriageState?.facility || "Emergency Triage Unit";
  const activeSeenAt = activeData?.seen_at || activeTriageState?.seen_at;
  const activeSeenBy = activeData?.seen_by || activeTriageState?.seen_by;
  const isCompleted = activeData?.is_completed || activeTriageState?.is_completed || activeData?.status === "completed";

  return (
    <div style={{ display: "flex", height: "calc(100vh - 65px)", overflow: "hidden" }}>
      {/* Left Sidebar - Session List */}
      <div className="nurse-sidebar-glass" style={{
        width: "320px", borderRight: "1px solid rgba(229, 231, 235, 0.8)",
        padding: "1rem", overflowY: "auto", flexShrink: 0
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div style={{ fontWeight: "700", fontSize: "0.9rem", color: "#374151" }}>
            Active Sessions ({sessionIds.length})
          </div>
          <button onClick={loadSessions} style={{
            fontSize: "0.75rem", background: "none", border: "1px solid #d1d5db",
            borderRadius: "4px", padding: "0.2rem 0.4rem", cursor: "pointer", color: "#6b7280"
          }}>
            ↻ Refresh
          </button>
        </div>

        {sessionIds.length === 0 ? (
          <p style={{ fontSize: "0.85rem", color: "#9ca3af", textAlign: "center", marginTop: "2rem" }}>
            No active sessions. Waiting for patients...
          </p>
        ) : (
          sessionIds.map(sid => (
            <SessionCard
              key={sid}
              sessionData={liveData[sid] || sessions[sid] || { session_id: sid, triage_state: {} }}
              onClick={() => handleSelectSession(sid)}
              isActive={activeSessionId === sid}
            />
          ))
        )}

        <div style={{ marginTop: "auto", paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>
            Signed in as <strong>{nurseInfo?.username || "nurse"}</strong>
          </div>
          <button className="btn btn-secondary" onClick={onLogout}
            style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem", width: "100%" }}>
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="nurse-main-glass" style={{ flex: 1, overflowY: "auto", padding: "1.25rem" }}>
        {!activeSessionId ? (
          <div style={{ textAlign: "center", color: "#9ca3af", marginTop: "4rem" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🩺</div>
            <p>Select a patient session from the left panel to view live information.</p>
          </div>
        ) : (
          <>
            {/* Session Header */}
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "flex-start",
              marginBottom: "1rem", background: "white", padding: "1rem", borderRadius: "8px",
              border: "1px solid #e5e7eb", boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <h2 style={{ fontSize: "1.3rem", fontWeight: "700", color: "#005691", margin: 0 }}>
                    👤 {activePatientName}
                  </h2>
                  {activeSeenAt ? (
                    <span style={{
                      fontSize: "0.75rem", background: "#dcfce7", color: "#15803d",
                      padding: "0.2rem 0.6rem", borderRadius: "12px", fontWeight: "600",
                      display: "flex", alignItems: "center", gap: "0.25rem", border: "1px solid #bbf7d0"
                    }}>
                      👁️ Seen {formatSeenTime(activeSeenAt)}
                    </span>
                  ) : (
                    <button
                      onClick={() => markSessionSeen(activeSessionId, nurseInfo?.username)}
                      style={{
                        fontSize: "0.75rem", background: "#fef3c7", color: "#92400e",
                        border: "1px solid #fde68a", padding: "0.2rem 0.6rem", borderRadius: "12px",
                        cursor: "pointer", fontWeight: "700"
                      }}
                    >
                      🔔 Mark as Seen
                    </button>
                  )}
                  {isCompleted && (
                    <span style={{
                      fontSize: "0.75rem", background: "#f0fdf4", color: "#166534",
                      padding: "0.2rem 0.6rem", borderRadius: "12px", fontWeight: "600", border: "1px solid #bbf7d0"
                    }}>
                      ✅ Intake Completed
                    </span>
                  )}
                </div>

                <div style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: "0.35rem" }}>
                  🏥 Facility: <strong>{activeFacility}</strong> &nbsp;|&nbsp;
                  Session: <strong>{activeSessionId}</strong> &nbsp;|&nbsp;
                  Language: <strong>{SUPPORTED_LANGUAGES.find(l => l.language_code === activeData.language)?.display_name || activeData.language || "Unknown"}</strong>
                  &nbsp;|&nbsp;
                  Status: <strong style={{ color: isCompleted ? "#0284c7" : "#16a34a" }}>{isCompleted ? "COMPLETED" : "LIVE"}</strong>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <ConnectionStatus status={connectionStatus} />
                <button
                  id="btn-delete-session"
                  className="btn btn-danger"
                  style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem", display: "flex", alignItems: "center", gap: "0.3rem" }}
                  onClick={handleDeleteSession}
                  disabled={isDeleting}
                >
                  🗑️ Delete Patient Record
                </button>
              </div>
            </div>

            {/* Red Flag Alert */}
            <RedFlagAlert redFlags={activeTriageState.red_flags || []} />

            {/* Two-column layout */}
            <div className="grid-2">
              {/* Left column */}
              <div>
                <TriageStatus triageState={activeTriageState} />
                <SummaryPanel
                  summary={activeTriageState.summary}
                  sessionId={activeSessionId}
                  language={activeData.language}
                  patientName={activePatientName}
                  facility={activeFacility}
                />
              </div>

              {/* Right column */}
              <div>
                <div className="card">
                  <div className="card-title">Live Transcript & Conversation</div>
                  <ConversationView messages={activeMessages} />
                </div>
                {activeTriageState.uncertainties?.length > 0 && (
                  <div className="card" style={{ background: "#fffbe6", border: "1px solid #ffe58f" }}>
                    <div className="card-title" style={{ color: "#873800" }}>Uncertainties Noted</div>
                    <ul style={{ paddingLeft: "1.2rem", fontSize: "0.9rem" }}>
                      {activeTriageState.uncertainties.map((u, i) => <li key={i}>{u}</li>)}
                    </ul>
                  </div>
                )}
                {activeTriageState.contradictions?.length > 0 && (
                  <div className="card" style={{ background: "#fff7f0", border: "1px solid #fdba74" }}>
                    <div className="card-title" style={{ color: "#c2410c" }}>Contradictions Flagged</div>
                    <ul style={{ paddingLeft: "1.2rem", fontSize: "0.9rem" }}>
                      {activeTriageState.contradictions.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            <p style={{ fontSize: "0.75rem", color: "#9ca3af", textAlign: "center", marginTop: "0.5rem" }}>
              Dashboard updates automatically via real-time WebSockets. Final clinical decision belongs to qualified medical staff.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
