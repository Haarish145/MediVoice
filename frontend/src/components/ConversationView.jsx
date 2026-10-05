import { formatTime } from "../utils/formatting";

export default function ConversationView({ messages = [] }) {
  if (messages.length === 0) {
    return (
      <div className="transcript-area" style={{ color: "#9ca3af", display: "flex", alignItems: "center", justifyContent: "center" }}>
        Conversation will appear here once you start speaking.
      </div>
    );
  }

  return (
    <div className="transcript-area" aria-live="polite" aria-label="Conversation transcript">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`chat-bubble ${msg.speaker === "patient" ? "patient" : "assistant"}`}
        >
          <div className="chat-speaker">
            {msg.speaker === "patient" ? "You" : "MediVoice"}
          </div>
          <div className="chat-text">{msg.original_text}</div>
          {msg.translated_text && msg.translated_text !== msg.original_text && (
            <div className="chat-translation">"{msg.translated_text}"</div>
          )}
          {msg.timestamp && (
            <div style={{ fontSize: "0.7rem", color: "#9ca3af", marginTop: "0.2rem" }}>
              {formatTime(msg.timestamp)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
