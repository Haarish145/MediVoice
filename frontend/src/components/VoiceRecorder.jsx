export default function VoiceRecorder({ isListening, isSupported, onStart, onStop, disabled }) {
  if (!isSupported) {
    return (
      <div style={{
        background: "#fef3c7", border: "1px solid #fcd34d",
        borderRadius: "8px", padding: "0.75rem", fontSize: "0.9rem", color: "#92400e"
      }}>
        ⚠ Speech recognition is not supported in this browser.
        Please use Chrome or Edge for voice input.
        You can still type responses using the text input below.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem" }}>
      <button
        id="mic-btn"
        className={`btn ${isListening ? "btn-danger" : "btn-primary"}`}
        style={{
          width: "80px", height: "80px", borderRadius: "50%",
          fontSize: "2rem", flexDirection: "column", gap: "0",
          padding: "0"
        }}
        onClick={isListening ? onStop : onStart}
        disabled={disabled}
        aria-label={isListening ? "Stop listening" : "Start listening"}
        aria-pressed={isListening}
      >
        {isListening ? "⏹" : "🎤"}
      </button>
      <div style={{ fontSize: "0.85rem", color: isListening ? "#dc2626" : "#6b7280", fontWeight: isListening ? 600 : 400 }}>
        {isListening ? "Listening... (tap to stop)" : "Tap microphone to speak"}
      </div>
    </div>
  );
}
