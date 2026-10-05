import { formatPriority } from "../utils/formatting";

export default function TriageStatus({ triageState }) {
  if (!triageState) return null;

  const { label, color } = formatPriority(triageState.priority);

  return (
    <div className="card">
      <div className="card-title">Triage Information</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
        {triageState.main_complaint && (
          <InfoItem label="Main Complaint" value={triageState.main_complaint} />
        )}
        {triageState.onset && (
          <InfoItem label="Onset" value={triageState.onset} />
        )}
        {triageState.duration && (
          <InfoItem label="Duration" value={triageState.duration} />
        )}
        {triageState.severity && (
          <InfoItem label="Severity" value={triageState.severity} />
        )}
        {triageState.symptoms?.length > 0 && (
          <InfoItem label="Symptoms" value={triageState.symptoms.join(", ")} />
        )}
        {triageState.associated_symptoms?.length > 0 && (
          <InfoItem label="Associated" value={triageState.associated_symptoms.join(", ")} />
        )}
      </div>
      {triageState.priority !== "unknown" && (
        <div style={{ marginTop: "0.75rem", display: "inline-block",
          background: color + "22", border: `1px solid ${color}`,
          color: color, padding: "0.3rem 0.8rem", borderRadius: "6px",
          fontSize: "0.85rem", fontWeight: "700" }}>
          {label}
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div style={{ minWidth: "120px" }}>
      <div style={{ fontSize: "0.75rem", color: "#6b7280", textTransform: "uppercase", fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: "0.9rem", color: "#1f2937", fontWeight: 500, marginTop: "0.2rem" }}>
        {value}
      </div>
    </div>
  );
}
