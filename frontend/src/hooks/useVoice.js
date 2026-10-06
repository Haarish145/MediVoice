import { useState, useEffect, useRef, useCallback } from "react";

const rawBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const BASE_URL = rawBaseUrl.replace(/\/+$/, "");

// Chrome Web Speech API supported Indian language locales for STT
const VOICE_SUPPORTED_LOCALES = new Set([
  "ta-IN", // Tamil ✅
  "hi-IN", // Hindi ✅
  "te-IN", // Telugu ✅
  "kn-IN", // Kannada ✅
  "ml-IN", // Malayalam ✅
  "bn-IN", // Bengali ✅
  "mr-IN", // Marathi ✅
  "gu-IN", // Gujarati ✅
  "en-US", // English ✅
]);

// Fallback locale for unsupported speech recognition languages
function getFallbackLocale(locale) {
  if (VOICE_SUPPORTED_LOCALES.has(locale)) return locale;
  return "hi-IN";
}

export function useVoice({ language = "en-US", onPartialTranscript, onFinalTranscript, onError }) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [isUsingFallback, setIsUsingFallback] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const recognitionRef = useRef(null);
  const currentAudioRef = useRef(null);
  const isSpeakingRef = useRef(false);
  const silenceTimeoutRef = useRef(null);
  const accumulatedTextRef = useRef("");

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);
    setIsUsingFallback(!VOICE_SUPPORTED_LOCALES.has(language));
  }, [language]);

  const stopListening = useCallback(() => {
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    const textToSend = accumulatedTextRef.current.trim();
    accumulatedTextRef.current = "";

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {}
      recognitionRef.current = null;
    }
    setIsListening(false);

    if (textToSend && textToSend.length >= 2) {
      onFinalTranscript?.(textToSend);
    }
  }, [onFinalTranscript]);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      onError?.("Speech recognition is not supported in this browser. Please use Google Chrome or type your response below.");
      return;
    }

    // Stop any speech playback while listening
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    isSpeakingRef.current = false;
    setIsSpeaking(false);

    // Stop any existing instance
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }

    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    accumulatedTextRef.current = "";

    const effectiveLocale = getFallbackLocale(language);
    const usingFallback = effectiveLocale !== language;

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = effectiveLocale;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsListening(true);
        if (usingFallback) {
          onError?.(`ℹ️ Voice input is using Hindi recognition for this language. You can also type below.`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
        const pending = accumulatedTextRef.current.trim();
        if (pending && pending.length >= 2) {
          accumulatedTextRef.current = "";
          onFinalTranscript?.(pending);
        }
      };

      recognition.onresult = (event) => {
        // Discard any sound picked up if system audio is actively playing
        if (isSpeakingRef.current) {
          return;
        }

        let currentInterim = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            const piece = transcript.trim();
            if (piece) {
              accumulatedTextRef.current = accumulatedTextRef.current
                ? `${accumulatedTextRef.current} ${piece}`
                : piece;
            }
          } else {
            currentInterim += transcript;
          }
        }

        const preview = (accumulatedTextRef.current + " " + currentInterim).trim();
        if (preview) {
          onPartialTranscript?.(preview);
        }

        // Debounce: wait for 1.3 seconds of natural silence before submitting response.
        // Prevents small pauses in speaking from cutting off the user mid-sentence!
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = setTimeout(() => {
          const finalFull = accumulatedTextRef.current.trim();
          if (finalFull && finalFull.length >= 2) {
            accumulatedTextRef.current = "";
            onFinalTranscript?.(finalFull);
            if (recognitionRef.current) {
              try { recognitionRef.current.stop(); } catch (e) {}
              recognitionRef.current = null;
            }
            setIsListening(false);
          }
        }, 1300);
      };

      recognition.onerror = (event) => {
        if (event.error === "no-speech") {
          return;
        }

        setIsListening(false);
        recognitionRef.current = null;
        if (event.error === "not-allowed") {
          onError?.("Microphone permission denied. Please allow microphone access or use text input below.");
        } else if (event.error === "language-not-supported") {
          onError?.("⚠️ Voice input not supported for this language. Please use the text input below.");
        } else if (event.error === "network") {
          onError?.("⚠️ Network error with speech recognition. Please type your response below.");
        } else {
          onError?.(`Speech note: ${event.error}. Please use text input.`);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setIsListening(false);
      recognitionRef.current = null;
      onError?.("Could not start microphone. You can type below.");
    }
  }, [language, onPartialTranscript, onFinalTranscript, onError]);

  // High-fidelity natural voice text-to-speech for all Indian languages
  const speakText = useCallback((text, lang = "en") => {
    if (!text || !text.trim()) return;

    // 1. Stop microphone listening immediately so mic does not hear speaker output
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
    setIsListening(false);

    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
    accumulatedTextRef.current = "";

    // 2. Cancel previous playback
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }

    const cleanLang = (lang || "en").split("-")[0].toLowerCase();
    const ttsUrl = `${BASE_URL}/api/tts?text=${encodeURIComponent(text.trim())}&language=${cleanLang}`;

    try {
      const audio = new Audio(ttsUrl);
      currentAudioRef.current = audio;
      isSpeakingRef.current = true;
      setIsSpeaking(true);

      audio.onended = () => {
        isSpeakingRef.current = false;
        setIsSpeaking(false);
        currentAudioRef.current = null;
      };

      audio.onerror = () => {
        // Fallback to browser SpeechSynthesis if network audio stream fails
        if (window.speechSynthesis) {
          try {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = VOICE_SUPPORTED_LOCALES.has(lang) ? lang : "hi-IN";
            utterance.rate = 0.95;
            utterance.onend = () => {
              isSpeakingRef.current = false;
              setIsSpeaking(false);
            };
            utterance.onerror = () => {
              isSpeakingRef.current = false;
              setIsSpeaking(false);
            };
            window.speechSynthesis.speak(utterance);
          } catch (e) {
            isSpeakingRef.current = false;
            setIsSpeaking(false);
          }
        } else {
          isSpeakingRef.current = false;
          setIsSpeaking(false);
        }
        currentAudioRef.current = null;
      };

      audio.play().catch(() => {
        // Fallback to Web Speech API
        if (window.speechSynthesis) {
          try {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = VOICE_SUPPORTED_LOCALES.has(lang) ? lang : "hi-IN";
            utterance.rate = 0.95;
            utterance.onend = () => {
              isSpeakingRef.current = false;
              setIsSpeaking(false);
            };
            utterance.onerror = () => {
              isSpeakingRef.current = false;
              setIsSpeaking(false);
            };
            window.speechSynthesis.speak(utterance);
          } catch (e) {
            isSpeakingRef.current = false;
            setIsSpeaking(false);
          }
        } else {
          isSpeakingRef.current = false;
          setIsSpeaking(false);
        }
      });
    } catch (e) {
      isSpeakingRef.current = false;
      setIsSpeaking(false);
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  }, []);

  return {
    isListening,
    isSupported,
    isUsingFallback,
    isSpeaking,
    startListening,
    stopListening,
    speakText,
    stopSpeaking
  };
}
