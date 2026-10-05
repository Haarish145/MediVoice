export default function RedFlagAlert({ redFlags }) {
  if (!redFlags || redFlags.length === 0) return null;

  return (
    <div className="red-flag-box" role="alert" aria-live="assertive">
      <div className="red-flag-title">
        <span>⚠</span>
        Possible High-Priority Symptoms Detected
      </div>
      <p style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>
        <strong>Nurse review required.</strong> The following screening rules were triggered:
      </p>
      {redFlags.map((flag, idx) => (
        <div key={idx} style={{
          borderTop: "1px solid #fca5a5",
          paddingTop: "0.4rem",
          marginTop: "0.4rem",
          fontSize: "0.85rem"
        }}>
          <strong>{flag.rule_name}</strong>
          <div style={{ color: "#7f1d1d", marginTop: "0.2rem" }}>{flag.reason}</div>
          {flag.triggered_symptoms?.length > 0 && (
            <div style={{ marginTop: "0.2rem", color: "#991b1b" }}>
              Matched: {flag.triggered_symptoms.join(", ")}
            </div>
          )}
          <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "0.2rem" }}>
            Ref: {flag.reference}
          </div>
        </div>
      ))}
      <p style={{ fontSize: "0.8rem", marginTop: "0.75rem", color: "#7f1d1d", fontStyle: "italic" }}>
        Final clinical decision remains with qualified medical staff.
      </p>
    </div>
  );
}
