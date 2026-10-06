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
  te: [
    { label: "Chest pain (5 mins) 🫀", text: "నాకు 5 నిమిషాల నుంచి గుండెల్లో నొప్పిగా ఉంది" },
    { label: "Breathing difficulty 🫁", text: "నాకు శ్వాస తీసుకోవడం చాలా కష్టంగా ఉంది" },
    { label: "Fever & Headache 🌡️", text: "నాకు తీవ్రమైన జ్వరం మరియు తలనొప్పి ఉంది" },
    { label: "Severe Pain 8/10 ⚡", text: "నొప్పి తీవ్రత 10 కి 8 గా ఉంది" },
    { label: "No other problem / Complete ✅", text: "ఇంకేమీ సమస్యలు లేవు, పూర్తి చేయవచ్చు" }
  ],
  kn: [
    { label: "Chest pain (5 mins) 🫀", text: "ನನಗೆ 5 ನಿಮಿಷಗಳಿಂದ ಎದೆ ನೋವು ಇದೆ" },
    { label: "Breathing difficulty 🫁", text: "ನನಗೆ ಉಸಿರಾಡಲು ತುಂಬಾ ಕಷ್ಟವಾಗುತ್ತಿದೆ" },
    { label: "Fever & Headache 🌡️", text: "ನನಗೆ ತೀವ್ರ ಜ್ವರ ಮತ್ತು ತಲೆನೋವು ಇದೆ" },
    { label: "Severe Pain 8/10 ⚡", text: "ನೋವಿನ ತೀವ್ರತೆ 10 ರಲ್ಲಿ 8 ರಷ್ಟಿದೆ" },
    { label: "No other problem / Complete ✅", text: "ಬೇರೆ ಯಾವುದೇ ಸಮಸ್ಯೆ ಇಲ್ಲ, ಮುಗಿಸಬಹುದು" }
  ],
  ml: [
    { label: "Chest pain (5 mins) 🫀", text: "എനിക്ക് 5 മിനിറ്റായി നെഞ്ചുവേദന അനുഭവപ്പെടുന്നു" },
    { label: "Breathing difficulty 🫁", text: "എനിക്ക് ശ്വാസമെടുക്കാൻ വളരെയധികം ബുദ്ധിമുട്ടുണ്ട്" },
    { label: "Fever & Headache 🌡️", text: "എനിക്ക് കഠിനമായ പനിയും തലവേദനയും ഉണ്ട്" },
    { label: "Severe Pain 8/10 ⚡", text: "വേദനയുടെ തീവ്രത 10-ൽ 8 ആണ്" },
    { label: "No other problem / Complete ✅", text: "വേറെ പ്രശ്നങ്ങളൊന്നുമില്ല, പൂർത്തിയാക്കാം" }
  ],
  bn: [
    { label: "Chest pain (5 mins) 🫀", text: "আমার ৫ মিনিট ধরে বুকে তীব্র ব্যথা হচ্ছে" },
    { label: "Breathing difficulty 🫁", text: "আমার শ্বাস নিতে খুব কষ্ট হচ্ছে" },
    { label: "Fever & Headache 🌡️", text: "আমার প্রচণ্ড জ্বর এবং মাথাব্যথা আছে" },
    { label: "Severe Pain 8/10 ⚡", text: "ব্যথার তীব্রতা ১০ এর মধ্যে ৮" },
    { label: "No other problem / Complete ✅", text: "অন্য কোনো সমস্যা নেই, সম্পন্ন করতে পারি" }
  ],
  mr: [
    { label: "Chest pain (5 mins) 🫀", text: "माझ्या छातीत ५ मिनिटांपासून तीव्र वेदना होत आहेत" },
    { label: "Breathing difficulty 🫁", text: "मला श्वास घेण्यास खूप त्रास होत आहे" },
    { label: "Fever & Headache 🌡️", text: "मला तीव्र ताप आणि डोकेदुखी आहे" },
    { label: "Severe Pain 8/10 ⚡", text: "वेदनांची तीव्रता १० पैकी ८ आहे" },
    { label: "No other problem / Complete ✅", text: "इतर कोणतीही समस्या नाही, पूर्ण करू शकता" }
  ],
  gu: [
    { label: "Chest pain (5 mins) 🫀", text: "મને ૫ મિનિટથી છાતીમાં દુખાવો થઈ રહ્યો છે" },
    { label: "Breathing difficulty 🫁", text: "મને શ્વાસ લેવામાં ખૂબ જ તકલીફ પડી રહી છે" },
    { label: "Fever & Headache 🌡️", text: "મને સખત તાવ અને માથાનો દુખાવો છે" },
    { label: "Severe Pain 8/10 ⚡", text: "દુખાવાની તીવ્રતા ૧૦ માંથી ૮ છે" },
    { label: "No other problem / Complete ✅", text: "અન્ય કોઈ તકલીફ નથી, પૂર્ણ કરી શકીએ છીએ" }
  ],
  pa: [
    { label: "Chest pain (5 mins) 🫀", text: "ਮੈਨੂੰ 5 ਮਿੰਟਾਂ ਤੋਂ ਛਾਤੀ ਵਿੱਚ ਤੇਜ਼ ਦਰਦ ਹੋ ਰਿਹਾ ਹੈ" },
    { label: "Breathing difficulty 🫁", text: "ਮੈਨੂੰ ਸਾਹ ਲੈਣ ਵਿੱਚ ਬਹੁਤ ਤਕਲੀਫ਼ ਹੋ ਰਹੀ ਹੈ" },
    { label: "Fever & Headache 🌡️", text: "ਮੈਨੂੰ ਤੇਜ਼ ਬੁਖ਼ਾਰ ਅਤੇ ਸਿਰਦਰਦ ਹੈ" },
    { label: "Severe Pain 8/10 ⚡", text: "ਦਰਦ ਦੀ ਗੰਭੀਰਤਾ 10 ਵਿੱਚੋਂ 8 ਹੈ" },
    { label: "No other problem / Complete ✅", text: "ਕੋਈ ਹੋਰ ਸਮੱਸਿਆ ਨਹੀਂ ਹੈ, ਪੂਰਾ ਕਰ ਸਕਦੇ ਹੋ" }
  ],
  or: [
    { label: "Chest pain (5 mins) 🫀", text: "ମୋତେ ୫ ମିନିଟ ଧରି ଛାତିରେ ଯନ୍ତ୍ରଣା ହେଉଛି" },
    { label: "Breathing difficulty 🫁", text: "ମୋତେ ନିଶ୍ୱାସ ନେବାରେ ବହୁତ କଷ୍ଟ ହେଉଛି" },
    { label: "Fever & Headache 🌡️", text: "ମୋତେ ପ୍ରବଳ ଜ୍ୱର ଏବଂ ମୁଣ୍ଡବିନ୍ଧା ଅଛି" },
    { label: "Severe Pain 8/10 ⚡", text: "ଯନ୍ତ୍ରଣା ୧୦ ରୁ ୮ ଅଟେ" },
    { label: "No other problem / Complete ✅", text: "ଆଉ କୌଣସି ସମସ୍ୟା ନାହିଁ, ସମାପ୍ତ କରିପାରିବା" }
  ],
  as: [
    { label: "Chest pain (5 mins) 🫀", text: "মোৰ ৫ মিনিট ধৰি বুকুত বিষ হৈ আছে" },
    { label: "Breathing difficulty 🫁", text: "মোৰ উশাহ লওঁতে বহুত কষ্ট হৈছে" },
    { label: "Fever & Headache 🌡️", text: "মোৰ তীব্ৰ জ্বৰ আৰু মূৰৰ বিষ হৈছে" },
    { label: "Severe Pain 8/10 ⚡", text: "বিষৰ মাত্ৰা ১০ ৰ ভিতৰত ৮" },
    { label: "No other problem / Complete ✅", text: "অন্য কোনো সমস্যা নাই, সমাপ্ত কৰিব পাৰো" }
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

  const { isListening, isSupported, isUsingFallback, isSpeaking, startListening, stopListening, speakText, stopSpeaking } = useVoice({
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
        speakText(data.followup_question, selectedLanguage);
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
      speakText(initQ, selectedLanguage);
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
    const quickPrompts = SAMPLE_SYMPTOMS[selectedLanguage] || SAMPLE_SYMPTOMS.en || [];

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
          <div className="card" style={{ background: "#f0f7ff", border: "1.5px solid #93c5fd", padding: "1.1rem", borderRadius: "12px", boxShadow: "0 2px 8px rgba(37,99,235,0.08)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#1d4ed8", fontWeight: 700, letterSpacing: "0.5px" }}>
                MEDIVOICE CLINICAL QUESTION
              </span>
              {isSpeaking && (
                <span style={{ fontSize: "0.72rem", color: "#2563eb", background: "#dbeafe", padding: "0.15rem 0.5rem", borderRadius: "12px", fontWeight: 600 }}>
                  🔊 Playing Audio...
                </span>
              )}
            </div>
            <p style={{ fontSize: "1.08rem", color: "#1e3a8a", fontWeight: 600, lineHeight: 1.5, margin: "0.2rem 0 0.6rem 0" }}>
              {currentQuestion}
            </p>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <button
                type="button"
                style={{
                  fontSize: "0.85rem",
                  background: isSpeaking ? "#2563eb" : "#e0e7ff",
                  color: isSpeaking ? "white" : "#1e40af",
                  border: "none",
                  borderRadius: "20px",
                  padding: "0.4rem 0.9rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  transition: "all 0.2s ease"
                }}
                onClick={() => {
                  if (isSpeaking) {
                    stopSpeaking();
                  } else {
                    speakText(currentQuestion, selectedLanguage);
                  }
                }}>
                {isSpeaking ? "⏹️ Stop Audio" : "🔊 Listen to Question"}
              </button>
            </div>
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
            isUsingFallback={isUsingFallback}
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
