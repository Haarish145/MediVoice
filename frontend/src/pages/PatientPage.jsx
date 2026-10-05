import { useState, useEffect, useCallback } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { useVoice } from "../hooks/useVoice";
import { useSession } from "../hooks/useSession";
import LanguageSelector from "../components/LanguageSelector";
import VoiceRecorder from "../components/VoiceRecorder";
import ConversationView from "../components/ConversationView";
import ConnectionStatus from "../components/ConnectionStatus";
import RedFlagAlert from "../components/RedFlagAlert";
import { SUPPORTED_LANGUAGES } from "../utils/languages";

const INITIAL_QUESTIONS = {
  ta: "உங்கள் உடல்நிலை பற்றி சொல்லுங்கள். என்ன பிரச்சனை உள்ளது?",
  hi: "आप कैसा महसूस कर रहे हैं? आपकी तकलीफ के बारे में बताएं।",
  te: "మీ ఆరోగ్య సమస్య గురించి చెప్పండి.",
  kn: "ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ಹೇಳಿ.",
  ml: "നിങ്ങളുടെ ആരോഗ്യ പ്രശ്നത്തെക്കുറിച്ച് പറയൂ.",
  bn: "আপনার স্বাস্থ্য সমস্যা সম্পর্কে বলুন।",
  mr: "तुमच्या आरोग्य समस्येबद्दल सांगा.",
  gu: "તમારી તકલીફ વિશે જણાવો.",
  pa: "ਆਪਣੀ ਸਿਹਤ ਸਮੱਸਿਆ ਬਾਰੇ ਦੱਸੋ।",
  or: "ଆପଣଙ୍କ ସ୍ୱାସ୍ଥ୍ୟ ସମସ୍ୟା ବିଷୟରେ କୁହନ୍ତୁ।",
  as: "আপোনাৰ স্বাস্থ্য সমস্যাৰ বিষয়ে কওক।",
  en: "Please describe what is troubling you today. What brings you here?"
};

const SAMPLE_SYMPTOMS = {
  ta: [
    { label: "Chest pain (5 mins) 🫀", text: "எனக்கு நெஞ்சு வலி 5 நிமிடங்களாக இருக்கிறது" },
    { label: "Breathing difficulty 🫁", text: "எனக்கு மூச்சு விடுவதில் சிரமமாக இருக்கிறது" },
    { label: "Fever & Headache 🌡️", text: "எனக்கு கடுமையான காய்ச்சல் மற்றும் தலைவலி உள்ளது" },
    { label: "Severe Pain 8/10 ⚡", text: "வலி மிகவும் கடுமையாக உள்ளது 8/10" },
    { label: "No other problem / Complete ✅", text: "வேறு எந்த பிரச்சனையும் இல்லை, முடித்துக் கொள்ளலாம்" }
  ],
  hi: [
    { label: "Chest pain (5 mins) 🫀", text: "मुझे 5 मिनट से सीने में दर्द हो रहा है" },
    { label: "Breathing difficulty 🫁", text: "मुझे सांस लेने में बहुत तकलीफ हो रही है" },
    { label: "Fever & Headache 🌡️", text: "मुझे तेज बुखार और सिरदर्द है" },
    { label: "Severe Pain 8/10 ⚡", text: "दर्द बहुत तेज है 8/10" },
    { label: "No other problem / Complete ✅", text: "कोई अन्य समस्या नहीं है, पूरा कर सकते हैं" }
  ],
  en: [
    { label: "Chest pain (5 mins) 🫀", text: "I have had sudden chest pain for 5 minutes" },
    { label: "Breathing difficulty 🫁", text: "I am having severe difficulty breathing" },
    { label: "Fever & Headache 🌡️", text: "I have a high fever and severe headache" },
    { label: "Severe Pain 8/10 ⚡", text: "The pain severity is 8 out of 10" },
    { label: "No other problem / Complete ✅", text: "No other problems, we can complete the session" }
  ]
};

export default function PatientPage() {
  const [screen, setScreen] = useState("welcome"); // welcome | registration | conversation | done
  const [selectedLanguage, setSelectedLanguage] = useState("ta");
  const [patientName, setPatientName] = useState("");
  const [facility, setFacility] = useState("Apollo Emergency Triage");
  const [triageState, setTriageState] = useState(null);
  const [messages, setMessages] = useState([]);
  const [redFlags, setRedFlags] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [partialText, setPartialText] = useState("");
  const [statusText, setStatusText] = useState("");
  const [textInput, setTextInput] = useState("");
  const { session, isCreating, error: sessionError, startSession } = useSession();
  const sessionId = session?.session_id;

  const { connectionStatus, lastEvent, sendMessage } = useWebSocket(
    "patient",
    screen === "conversation" ? sessionId : null
  );

  const langLocale = SUPPORTED_LANGUAGES.find(l => l.language_code === selectedLanguage)?.locale || "en-US";

  const handleSendText = useCallback((text) => {
    if (!text?.trim() || !sessionId) return;
    setStatusText("Processing symptoms...");
    sendMessage({
      event: "patient_speech_final",
      data: { text: text.trim(), language: selectedLanguage }
    });
  }, [sessionId, selectedLanguage, sendMessage]);

  const { isListening, isSupported, startListening, stopListening, speakText } = useVoice({
    language: langLocale,
    onPartialTranscript: (text) => setPartialText(text),
    onFinalTranscript: (text) => {
      setPartialText("");
      handleSendText(text);
    },
    onError: (err) => setStatusText(err)
  });

  // Handle incoming real-time WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    const { event, data } = lastEvent;

    if (event === "ai_processing") {
      setStatusText("Analyzing clinical intake...");
    } else if (event === "session_completed" || data?.is_completed) {
      setStatusText("Intake session complete!");
      if (data?.triage_state) setTriageState(data.triage_state);
      setTimeout(() => {
        setScreen("done");
      }, 1000);
    } else if (event === "triage_state_updated") {
      setTriageState(data.triage_state);
      
      // Update full conversation history
      if (data.messages && data.messages.length > 0) {
        setMessages(data.messages);
      } else if (data.patient_message) {
        setMessages(prev => {
          const exists = prev.some(m => m.id === data.patient_message.id);
          return exists ? prev : [...prev, data.patient_message];
        });
      }

      if (data.is_completed) {
        setStatusText("Intake session complete!");
        setTimeout(() => setScreen("done"), 1000);
      } else if (data.followup_question) {
        setCurrentQuestion(data.followup_question);
        speakText(data.followup_question, langLocale);
      }
      setStatusText("");
    } else if (event === "red_flag_detected") {
      setRedFlags(data.red_flags || []);
    }
  }, [lastEvent, langLocale, speakText]);

  const handleStartSession = async () => {
    const s = await startSession(selectedLanguage, patientName, facility);
    if (s) {
      const initQ = INITIAL_QUESTIONS[selectedLanguage] || INITIAL_QUESTIONS.en;
      setCurrentQuestion(initQ);
      setMessages([{ id: 0, speaker: "assistant", original_text: initQ, timestamp: new Date().toISOString() }]);
      setScreen("conversation");
      // Read initial question out loud
      speakText(initQ, langLocale);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    handleSendText(textInput.trim());
    setTextInput("");
  };

  if (screen === "welcome") {
    return (
      <div className="main-container" style={{ maxWidth: "480px" }}>
        <div className="card" style={{ textAlign: "center", padding: "2.5rem 1.5rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.75rem" }}>🏥</div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: "700", color: "#005691", marginBottom: "0.5rem" }}>
            MediVoice
          </h1>
          <p style={{ color: "#6b7280", fontSize: "0.95rem", marginBottom: "0.5rem" }}>
            Emergency Intake & Triage Assistant
          </p>
          <p style={{ color: "#374151", fontSize: "0.9rem", marginBottom: "2rem", lineHeight: "1.6" }}>
            Communicate acute symptoms in your preferred regional language. 
            Real-time translation and clinical red-flag screening are provided to the triage nurse.
          </p>
          <button className="btn btn-primary" style={{ width: "100%", padding: "0.9rem" }}
            onClick={() => setScreen("registration")} id="btn-get-started">
            Begin Intake →
          </button>
          <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#9ca3af" }}>
            For immediate life-threatening danger, alert the emergency desk directly.
          </p>
        </div>
      </div>
    );
  }

  if (screen === "registration") {
    return (
      <div className="main-container" style={{ maxWidth: "600px" }}>
        <div className="card">
          <div className="card-title">Patient Intake Details / நோயாளி விவரங்கள்</div>
          
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#374151", marginBottom: "0.3rem" }}>
              Patient Name / நோயாளி பெயர்
            </label>
            <input
              id="patient-name-input"
              className="input-field"
              type="text"
              value={patientName}
              onChange={e => setPatientName(e.target.value)}
              placeholder="e.g. Ramesh Kumar / ரமேஷ் குமார் (optional)"
            />
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#374151", marginBottom: "0.3rem" }}>
              Facility / Hospital / மருத்துவமனை
            </label>
            <input
              id="facility-input"
              className="input-field"
              type="text"
              value={facility}
              onChange={e => setFacility(e.target.value)}
              placeholder="e.g. Apollo Emergency / Govt General Hospital"
            />
          </div>

          <div style={{ borderTop: "1px solid #e5e7eb", paddingTop: "1rem", marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: "600", color: "#374151", marginBottom: "0.6rem" }}>
              Select Language / மொழியை தேர்ந்தெடுக்கவும்
            </label>
            <LanguageSelector selected={selectedLanguage} onSelect={setSelectedLanguage} />
          </div>

          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
            <button className="btn btn-secondary" onClick={() => setScreen("welcome")}>Back</button>
            <button className="btn btn-primary" id="btn-continue-lang"
              onClick={handleStartSession} disabled={isCreating} style={{ flex: 1 }}>
              {isCreating ? "Connecting..." : "Start Intake Session →"}
            </button>
          </div>
          {sessionError && (
            <div style={{ marginTop: "0.75rem", color: "#dc2626", fontSize: "0.9rem" }}>
              {sessionError}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (screen === "conversation") {
    const quickPrompts = SAMPLE_SYMPTOMS[selectedLanguage] || SAMPLE_SYMPTOMS.ta;

    return (
      <div className="main-container" style={{ maxWidth: "600px" }}>
        {/* Session Header Badge */}
        <div style={{
          background: "white", padding: "0.8rem 1rem", borderRadius: "8px",
          border: "1px solid #e5e7eb", marginBottom: "1rem",
          display: "flex", justifyContent: "space-between", alignItems: "center"
        }}>
          <div>
            <div style={{ fontWeight: "700", color: "#005691", fontSize: "1.05rem" }}>
              {patientName ? `Patient: ${patientName}` : "Patient Intake"}
            </div>
            <div style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "0.15rem" }}>
              🏥 {facility || "Emergency Facility"} &nbsp;|&nbsp; 
              🗣️ {SUPPORTED_LANGUAGES.find(l => l.language_code === selectedLanguage)?.display_name}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginBottom: "0.2rem" }}>{sessionId}</div>
            <ConnectionStatus status={connectionStatus} />
          </div>
        </div>

        {/* Red Flag Alert Banner */}
        <RedFlagAlert redFlags={redFlags} />

        {/* Current Active Question */}
        {currentQuestion && (
          <div className="card" style={{ background: "#e6f0fa", border: "1px solid #bfdbfe", padding: "1rem" }}>
            <div style={{ fontSize: "0.75rem", color: "#1e40af", fontWeight: 700, letterSpacing: "0.5px", marginBottom: "0.3rem" }}>
              MEDIVOICE FOLLOW-UP QUESTION
            </div>
            <p style={{ fontSize: "1.05rem", color: "#1e3a8a", fontWeight: 600, lineHeight: 1.5 }}>
              {currentQuestion}
            </p>
            <button style={{
              marginTop: "0.5rem", fontSize: "0.8rem", background: "none",
              border: "none", color: "#2563eb", cursor: "pointer", padding: 0, fontWeight: 500
            }}
              onClick={() => speakText(currentQuestion, langLocale)}>
              🔊 Listen again
            </button>
          </div>
        )}

        {/* Live Conversation Transcript */}
        <div className="card">
          <div className="card-title">Live Intake Transcript</div>
          <ConversationView messages={messages} />
          {partialText && (
            <div style={{ fontSize: "0.9rem", color: "#9ca3af", fontStyle: "italic", padding: "0.5rem 0" }}>
              {partialText}...
            </div>
          )}
        </div>

        {/* Voice Input Section */}
        <div className="card" style={{ textAlign: "center", padding: "1.25rem" }}>
          <VoiceRecorder
            isListening={isListening}
            isSupported={isSupported}
            onStart={startListening}
            onStop={stopListening}
            disabled={connectionStatus !== "connected"}
          />
          {statusText && (
            <p style={{ marginTop: "0.6rem", fontSize: "0.85rem", color: "#005691", fontWeight: 500 }}>
              {statusText}
            </p>
          )}
        </div>

        {/* Quick Symptom Test Buttons (Great for instant testing) */}
        <div className="card" style={{ background: "#f8fafc", padding: "0.9rem" }}>
          <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600, marginBottom: "0.5rem" }}>
            Quick Prompts / விரைவு அறிகுறிகள் (Tap to Send):
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem", borderRadius: "16px" }}
                onClick={() => handleSendText(p.text)}
                disabled={connectionStatus !== "connected"}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Text Input Fallback */}
        <div className="card">
          <div style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>
            Or type your response manually:
          </div>
          <form onSubmit={handleTextSubmit} style={{ display: "flex", gap: "0.5rem" }}>
            <input
              className="input-field"
              style={{ margin: 0 }}
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              placeholder="Type your symptoms here..."
              id="text-input"
            />
            <button
              type="submit"
              className="btn btn-primary"
              style={{ whiteSpace: "nowrap" }}
              disabled={!textInput.trim() || connectionStatus !== "connected"}
            >
              Send
            </button>
          </form>
        </div>

        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <button className="btn btn-secondary" onClick={() => setScreen("done")} id="btn-end-session">
            Complete Intake Session
          </button>
        </div>
      </div>
    );
  }

  if (screen === "done") {
    return (
      <div className="main-container" style={{ maxWidth: "480px" }}>
        <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.75rem" }}>✅</div>
          <h2 style={{ color: "#005691", marginBottom: "0.5rem" }}>Intake Complete</h2>
          <p style={{ color: "#4b5563", marginBottom: "1.5rem", fontSize: "0.95rem" }}>
            Thank you, {patientName || "Patient"}. The triage nurse has received your structured summary at {facility}.
          </p>
          <p style={{ fontSize: "0.8rem", color: "#9ca3af" }}>Session ID: {sessionId}</p>
          <button className="btn btn-primary" style={{ marginTop: "1rem", width: "100%" }}
            onClick={() => { setScreen("welcome"); setMessages([]); setRedFlags([]); setTriageState(null); }}>
            Start New Session
          </button>
        </div>
      </div>
    );
  }

  return null;
}
