export default function SummaryPanel({ summary, sessionId, language, patientName, facility }) {
  if (!summary) return null;

  return (
    <div className="card">
      <div className="card-title">English Triage Summary</div>
      <div style={{
        display: "flex", flexWrap: "wrap", gap: "0.5rem 1rem",
        fontSize: "0.8rem", color: "#4b5563", marginBottom: "0.75rem",
        background: "#f1f5f9", padding: "0.5rem 0.75rem", borderRadius: "6px"
      }}>
        {patientName && (
          <div>Patient: <strong>{patientName}</strong></div>
        )}
        {facility && (
          <div>Facility: <strong>{facility}</strong></div>
        )}
        {sessionId && (
          <div>Session: <strong>{sessionId}</strong></div>
        )}
        {language && (
          <div>Language: <strong>{language?.toUpperCase()}</strong></div>
        )}
      </div>
      <p style={{
        fontSize: "0.95rem", lineHeight: "1.7", color: "#1f2937",
        background: "#ffffff", padding: "0.85rem", borderRadius: "6px",
        border: "1px solid #e2e8f0", borderLeft: "4px solid #005691"
      }}>
        {summary}
      </p>
      <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "0.5rem", fontStyle: "italic" }}>
        This summary is for communication support only. Final clinical assessment must be made by qualified medical staff.
      </p>
    </div>
  );
}
