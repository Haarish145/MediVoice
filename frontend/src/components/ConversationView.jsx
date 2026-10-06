import { useEffect, useRef } from "react";
import { formatTime } from "../utils/formatting";

export default function ConversationView({ messages = [], nurseView = false }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="transcript-area" style={{ color: "#9ca3af", display: "flex", alignItems: "center", justifyContent: "center" }}>
        Conversation will appear here once you start speaking.
      </div>
    );
  }

  return (
    <div className="transcript-area" aria-live="polite" aria-label="Conversation transcript">
      {messages.map((msg, idx) => {
        const isPatient = msg.speaker === "patient";
        const hasTranslation = msg.translated_text && msg.translated_text !== msg.original_text;

        // In nurse view: patient messages show English translation prominently
        // In patient view: always show original text (the regional language)
        let primaryText = msg.original_text;
        let secondaryText = null;

        if (nurseView && isPatient && hasTranslation) {
          primaryText = msg.translated_text;
          secondaryText = msg.original_text;
        } else if (!nurseView && hasTranslation) {
          secondaryText = msg.translated_text;
        }

        return (
          <div
            key={idx}
            className={`chat-bubble ${isPatient ? "patient" : "assistant"}`}
          >
            <div className="chat-speaker">
              {isPatient ? (nurseView ? "Patient" : "You") : "MediVoice"}
            </div>
            <div className="chat-text">{primaryText}</div>
            {secondaryText && (
              <div className="chat-translation">
                {nurseView && isPatient ? `[Original: ${secondaryText}]` : `"${secondaryText}"`}
              </div>
            )}
            {msg.timestamp && (
              <div style={{ fontSize: "0.7rem", color: "#9ca3af", marginTop: "0.2rem" }}>
                {formatTime(msg.timestamp)}
              </div>
            )}
          </div>
        );
      })}
      <div ref={messagesEndRef} style={{ height: "1px" }} />
    </div>
  );
}
