from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

SUPPORTED_LANGUAGES: List[Dict[str, Any]] = [
    {
        "language_code": "ta",
        "display_name": "தமிழ் (Tamil)",
        "locale": "ta-IN",
        "speech_recognition_code": "ta-IN",
        "speech_synthesis_code": "ta-IN",
        "translation_code": "ta",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "hi",
        "display_name": "हिन्दी (Hindi)",
        "locale": "hi-IN",
        "speech_recognition_code": "hi-IN",
        "speech_synthesis_code": "hi-IN",
        "translation_code": "hi",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "te",
        "display_name": "తెలుగు (Telugu)",
        "locale": "te-IN",
        "speech_recognition_code": "te-IN",
        "speech_synthesis_code": "te-IN",
        "translation_code": "te",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "kn",
        "display_name": "ಕನ್ನಡ (Kannada)",
        "locale": "kn-IN",
        "speech_recognition_code": "kn-IN",
        "speech_synthesis_code": "kn-IN",
        "translation_code": "kn",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "ml",
        "display_name": "മലയാളം (Malayalam)",
        "locale": "ml-IN",
        "speech_recognition_code": "ml-IN",
        "speech_synthesis_code": "ml-IN",
        "translation_code": "ml",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "bn",
        "display_name": "বাংলা (Bengali)",
        "locale": "bn-IN",
        "speech_recognition_code": "bn-IN",
        "speech_synthesis_code": "bn-IN",
        "translation_code": "bn",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "mr",
        "display_name": "मराठी (Marathi)",
        "locale": "mr-IN",
        "speech_recognition_code": "mr-IN",
        "speech_synthesis_code": "mr-IN",
        "translation_code": "mr",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "gu",
        "display_name": "ગુજરાતી (Gujarati)",
        "locale": "gu-IN",
        "speech_recognition_code": "gu-IN",
        "speech_synthesis_code": "gu-IN",
        "translation_code": "gu",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "pa",
        "display_name": "ਪੰਜਾਬੀ (Punjabi)",
        "locale": "pa-IN",
        "speech_recognition_code": "pa-IN",
        "speech_synthesis_code": "pa-IN",
        "translation_code": "pa",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "or",
        "display_name": "ଓଡ଼ିଆ (Odia)",
        "locale": "or-IN",
        "speech_recognition_code": "or-IN",
        "speech_synthesis_code": "or-IN",
        "translation_code": "or",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "as",
        "display_name": "অসমীয়া (Assamese)",
        "locale": "as-IN",
        "speech_recognition_code": "as-IN",
        "speech_synthesis_code": "as-IN",
        "translation_code": "as",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    },
    {
        "language_code": "en",
        "display_name": "English",
        "locale": "en-US",
        "speech_recognition_code": "en-US",
        "speech_synthesis_code": "en-US",
        "translation_code": "en",
        "supported_capabilities": ["stt", "tts", "translation", "adaptive_questions"]
    }
]

@router.get("/languages")
def get_languages():
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "total_languages": len(SUPPORTED_LANGUAGES)
    }
