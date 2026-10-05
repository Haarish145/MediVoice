import { useState, useEffect, useRef, useCallback } from "react";

export function useVoice({ language = "en-US", onPartialTranscript, onFinalTranscript, onError }) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // Ignore if already stopped
      }
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  const startListening = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      onError?.("Speech recognition is not supported in this browser. Please use Google Chrome or type your response below.");
      return;
    }

    // Stop any existing instance
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = language;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => setIsListening(true);
      
      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };

      recognition.onresult = (event) => {
        let interimText = "";
        let finalText = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalText += transcript;
          } else {
            interimText += transcript;
          }
        }

        if (interimText) onPartialTranscript?.(interimText);
        if (finalText) onFinalTranscript?.(finalText);
      };

      recognition.onerror = (event) => {
        setIsListening(false);
        recognitionRef.current = null;
        if (event.error === "not-allowed") {
          onError?.("Microphone permission denied. Please allow microphone access or use text input below.");
        } else if (event.error === "no-speech") {
          // Normal pause, don't crash
        } else {
          onError?.(`Speech recognition note: ${event.error}`);
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

  const speakText = useCallback((text, lang = "en-US") => {
    if (!window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    } catch (e) {}
  }, []);

  return { isListening, isSupported, startListening, stopListening, speakText };
}
