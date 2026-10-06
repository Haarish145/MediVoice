import logging
import urllib.parse
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("medivoice.tts")

# Maps ISO language codes to Google TTS supported 'tl' codes
# Note: For Odia ('or') and Assamese ('as'), high-similarity Indian phonetics are used (hi/bn)
LANG_TO_TTS_CODE = {
    "ta": "ta",   # Tamil
    "hi": "hi",   # Hindi
    "te": "te",   # Telugu
    "kn": "kn",   # Kannada
    "ml": "ml",   # Malayalam
    "bn": "bn",   # Bengali
    "mr": "mr",   # Marathi
    "gu": "gu",   # Gujarati
    "pa": "pa",   # Punjabi
    "en": "en",   # English
    "or": "hi",   # Odia (phonetic fallback)
    "as": "bn",   # Assamese (Eastern Nagari phonetic match)
}

class TTSService:
    """
    Robust Text-to-Speech service for all Indian regional languages.
    Fetches natural voice MP3 audio and caches responses in memory.
    """
    def __init__(self):
        self._cache: Dict[str, bytes] = {}

    def _normalize_lang(self, language: str) -> str:
        if not language:
            return "en"
        code = language.split("-")[0].split("_")[0].lower()
        return LANG_TO_TTS_CODE.get(code, "en")

    async def get_audio_bytes(self, text: str, language: str = "en") -> Optional[bytes]:
        if not text or not text.strip():
            return None

        cleaned_text = text.strip()
        tts_lang = self._normalize_lang(language)
        cache_key = f"{tts_lang}:{cleaned_text}"

        # 1. Return cached audio if available
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Fetch high-quality natural voice audio from Google TTS endpoint
        try:
            encoded_text = urllib.parse.quote(cleaned_text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={tts_lang}&client=tw-ob"
            
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://translate.google.com/"
                })
                if resp.status_code == 200 and len(resp.content) > 500:
                    self._cache[cache_key] = resp.content
                    logger.info(f"Synthesized TTS audio ({len(resp.content)} bytes) for [{tts_lang}]: {cleaned_text[:30]}...")
                    return resp.content
                else:
                    logger.warning(f"Google TTS returned status {resp.status_code} for [{tts_lang}]")
        except Exception as e:
            logger.error(f"TTS synthesis error for language {language}: {e}")

        return None

    async def synthesize(self, text: str, language: str) -> Dict[str, Any]:
        """Metadata response for API compatibility"""
        tts_lang = self._normalize_lang(language)
        return {
            "text": text,
            "language": language,
            "tts_lang": tts_lang,
            "audio_url": f"/api/tts?text={urllib.parse.quote(text)}&language={language}",
            "status": "completed"
        }

tts_service = TTSService()
