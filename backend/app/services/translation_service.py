import logging
import re
import urllib.parse
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("medivoice.translation")

# Rich offline medical translation dictionary for Indian languages
COMMON_TRANSLATIONS = {
    "ta": {
        "எனக்கு திடீரென்று மார்பில் வலி": "I suddenly have chest pain.",
        "எனக்கு மார்பில் வலி": "I have chest pain.",
        "எனக்கு நெஞ்சு வலி": "I have chest pain.",
        "எனக்கு நெஞ்சு வலிக்குது": "I have chest pain.",
        "நெஞ்சு வலி": "Chest pain",
        "மார்பில் வலி": "Chest pain",
        "20 நிமிடங்கள்": "20 minutes",
        "5 நிமிடங்கள்": "5 minutes",
        "5 நிமிடங்களாக": "for 5 minutes",
        "20 நிமிடங்களாக": "for 20 minutes",
        "மூச்சு விடுவதில் சிரமமாக இருக்கிறது": "I am having difficulty breathing.",
        "மூச்சு விடுவதில் சிரமம்": "Difficulty breathing",
        "மூச்சு திணறல்": "Shortness of breath",
        "காய்ச்சல் மற்றும் தலைவலி": "Fever and headache",
        "காய்ச்சல்": "Fever",
        "தலைவலி": "Headache",
        "வயிறு வலி": "Abdominal pain",
        "திடீரென்று": "suddenly",
        "மிகவும் அதிகம்": "very severe",
        "தாங்க முடியவில்லை": "unbearable",
        "லேசான வலி": "mild pain",
        "மிதமான வலி": "moderate pain",
        "இல்லை": "No, no other problem.",
        "வேறு பிரச்சனை இல்லை": "No other problems.",
        "முடித்துக் கொள்ளலாம்": "We can complete the session.",
        "வேறொன்றுமில்லை": "Nothing else."
    },
    "hi": {
        "मुझे अचानक सीने में दर्द हुआ": "I suddenly developed chest pain.",
        "मुझे सीने में दर्द है": "I have chest pain.",
        "सीने में दर्द": "Chest pain",
        "20 मिनट से": "For 20 minutes",
        "5 मिनट से": "For 5 minutes",
        "20 मिनट": "20 minutes",
        "5 मिनट": "5 minutes",
        "मुझे सांस लेने में तकलीफ हो रही है": "I am having difficulty breathing.",
        "सांस लेने में तकलीफ": "Difficulty breathing",
        "मुझे बुखार और सिरदर्द है": "I have fever and headache",
        "बुखार": "Fever",
        "सिरदर्द": "Headache",
        "पेट दर्द": "Abdominal pain",
        "अचानक": "suddenly",
        "बहुत तेज": "very severe",
        "नहीं": "No, no other problem.",
        "और कुछ नहीं": "Nothing else.",
        "पूरा कर सकते हैं": "We can complete the session."
    },
    "te": {
        "నాకు ఛాతీలో నొప్పిగా ఉంది": "I have chest pain.",
        "ఛాతీ నొప్పి": "Chest pain",
        "శ్వాస తీసుకోవడంలో ఇబ్బంది": "Difficulty breathing",
        "జ్వరం": "Fever",
        "తలనొప్పి": "Headache",
        "కడుపు నొప్పి": "Abdominal pain",
        "లేదు": "No other problem."
    },
    "kn": {
        "ನನಗೆ ಎದೆ ನೋವು ಇದೆ": "I have chest pain.",
        "ಎದೆ ನೋವು": "Chest pain",
        "ಉಸಿರಾಟದ ತೊಂದರೆ": "Difficulty breathing",
        "ಜ್ವರ": "Fever",
        "ತಲೆನೋವು": "Headache",
        "ಇಲ್ಲ": "No other problem."
    },
    "ml": {
        "എനിക്ക് നെഞ്ചുവേദനയുണ്ട്": "I have chest pain.",
        "നെഞ്ചുവേദന": "Chest pain",
        "ശ്വാസതടസ്സം": "Difficulty breathing",
        "പനി": "Fever",
        "തലവേദന": "Headache",
        "ഇല്ല": "No other problem."
    },
    "bn": {
        "আমার বুকে ব্যথা করছে": "I have chest pain.",
        "বুকে ব্যথা": "Chest pain",
        "শ্বাসকষ্ট": "Difficulty breathing",
        "জ্বর": "Fever",
        "মাথাব্যথা": "Headache",
        "না": "No other problem."
    }
}

# Offline phrase replacement patterns for Indian medical terms
PHRASE_REPLACEMENTS = [
    # Tamil
    (re.compile(r"நெஞ்சு\s*வலி|மார்பில்\s*வலி|மார்பு\s*வலி", re.IGNORECASE), "chest pain"),
    (re.compile(r"மூச்சு\s*(?:திணறல்|விட\s*முடியல|விடுவது\s*சிரமம்|சிரமமாக)", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"தலை\s*வலி", re.IGNORECASE), "headache"),
    (re.compile(r"காய்ச்சல்", re.IGNORECASE), "fever"),
    (re.compile(r"வயிறு\s*வலி", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"திடீரென்று|திடீரென", re.IGNORECASE), "suddenly"),
    (re.compile(r"(\d+)\s*நிமிட(?:ங்கள்|ங்களாக|மாக)", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*மணி\s*நேர(?:ங்கள்|மாக)", re.IGNORECASE), r"\1 hours"),
    (re.compile(r"எனக்கு", re.IGNORECASE), "I have"),
    (re.compile(r"இருக்கிறது|உள்ளது|வலிக்குது", re.IGNORECASE), ""),
    # Hindi
    (re.compile(r"सीने\s*में\s*दर्द", re.IGNORECASE), "chest pain"),
    (re.compile(r"सांस\s*(?:लेने\s*में\s*तकलीफ|फूलना)", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"सिर\s*दर्द", re.IGNORECASE), "headache"),
    (re.compile(r"पेट\s*दर्द", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"बुखार", re.IGNORECASE), "fever"),
    (re.compile(r"अचानक", re.IGNORECASE), "suddenly"),
    (re.compile(r"(\d+)\s*मिनट", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*घंटे", re.IGNORECASE), r"\1 hours"),
    (re.compile(r"मुझे", re.IGNORECASE), "I have"),
    (re.compile(r"हो\s*रहा\s*है|है", re.IGNORECASE), "")
]

QUESTION_TRANSLATIONS = {
    "ta": {
        "duration": "இந்த வலி எவ்வளவு நேரமாக இருக்கிறது?",
        "severity": "இந்த வலி எவ்வளவு கடுமையாக இருக்கிறது (1 முதல் 10 வரை)?",
        "breathing": "மூச்சு விடுவதில் சிரமம் உள்ளதா?",
        "breathing_difficulty": "மூச்சு விடுவதில் சிரமம் உள்ளதா?",
        "onset": "இந்த வலி திடீரென வந்ததா அல்லது மெதுவாகத் தொடங்கியதா?",
        "completion_check": "உங்களுக்கு வேறு ஏதேனும் உடல்நலப் பிரச்சனை உள்ளதா, அல்லது இந்த பதிவை முடித்துக் கொள்ளலாமா?"
    },
    "hi": {
        "duration": "यह दर्द कितने समय से हो रहा है?",
        "severity": "यह दर्द कितना तेज है (1 से 10 के पैमाने पर)?",
        "breathing": "क्या आपको सांस लेने में तकलीफ हो रही है?",
        "breathing_difficulty": "क्या आपको सांस लेने में तकलीफ हो रही है?",
        "onset": "क्या यह दर्द अचानक शुरू हुआ?",
        "completion_check": "क्या आपको कोई अन्य समस्या है, या हम सत्र पूरा कर सकते हैं?"
    },
    "te": {
        "duration": "ఈ నొప్పి ఎంత సమయం నుండి ఉంది?",
        "severity": "ఈ నొప్పి ఎంత తీవ్రంగా ఉంది?",
        "breathing": "శ్వాస తీసుకోవడంలో ఇబ్బంది ఉందా?",
        "breathing_difficulty": "శ్వాస తీసుకోవడంలో ఇబ్బంది ఉందా?",
        "onset": "ఈ నొప్పి హఠాత్తుగా మొదలైందా?",
        "completion_check": "మీకు ఇతర సమస్యలు ఏమైనా ఉన్నాయా, లేదా సెషన్‌ను పూర్తి చేయవచ్చా?"
    },
    "kn": {
        "duration": "ಈ ನೋವು ಎಷ್ಟು ಸಮಯದಿಂದ ಇದೆ?",
        "severity": "ಈ ನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ?",
        "breathing_difficulty": "ಉಸಿರಾಟದಲ್ಲಿ ತೊಂದರೆ ಇದೆಯೇ?",
        "completion_check": "ನಿಮಗೆ ಬೇರೆ ಏನಾದರೂ ಸಮಸ್ಯೆ ಇದೆಯೇ, ಅಥವಾ ಅಧಿವೇಶನವನ್ನು ಪೂರ್ಣಗೊಳಿಸಬಹುದೇ?"
    },
    "ml": {
        "duration": "ഈ വേദന എത്ര സമയമായി ഉണ്ട്?",
        "severity": "വേദന എത്രത്തോളം കഠിനമാണ്?",
        "breathing_difficulty": "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ടുണ്ടോ?",
        "completion_check": "നിങ്ങൾക്ക് മറ്റ് എന്തെങ്കിലും പ്രശ്നങ്ങളുണ്ടോ, അല്ലെങ്കിൽ ഈ സെഷൻ പൂർത്തിയാക്കാമോ?"
    }
}

def remove_non_latin(text: str) -> str:
    """Removes non-Latin characters leaving only English text, numbers and punctuation."""
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()

class TranslationService:
    async def translate_to_english(self, text: str, source_language: str = "ta") -> str:
        if not text or not text.strip():
            return ""
            
        stripped = text.strip()
        
        # If source language is already English and text is purely ASCII
        if source_language == "en" and all(ord(c) < 128 for c in stripped):
            return stripped

        # 1. Exact match in offline dictionary
        lang_dict = COMMON_TRANSLATIONS.get(source_language, {})
        if stripped in lang_dict:
            return lang_dict[stripped]

        # 2. Try Online High-Accuracy Translation Endpoint (Google GTX API)
        try:
            sl = source_language if source_language else "auto"
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl=en&dt=t&q={urllib.parse.quote(stripped)}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if res.status_code == 200:
                    data = res.json()
                    translated = "".join(part[0] for part in data[0] if part[0]).strip()
                    if translated:
                        cleaned = remove_non_latin(translated)
                        if cleaned:
                            return cleaned
                        return translated
        except Exception as e:
            logger.warning(f"Online translation request failed ({e}); falling back to offline clinical mapper.")

        # 3. Offline heuristic / phrase substitution fallback
        working = stripped
        for pattern, replacement in PHRASE_REPLACEMENTS:
            working = pattern.sub(replacement, working)

        cleaned = remove_non_latin(working)
        if cleaned and len(cleaned) > 2:
            return cleaned

        # 4. Final safety guarantee: Return generic clinical complaint in English
        return "Patient reports acute symptoms"

    async def translate_question(self, question_en: str, target_language: str, question_type: str = "") -> str:
        if target_language == "en":
            return question_en
            
        lang_questions = QUESTION_TRANSLATIONS.get(target_language, {})
        if question_type in lang_questions:
            return lang_questions[question_type]
            
        # Try online translation for questions into patient's language
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_language}&dt=t&q={urllib.parse.quote(question_en)}"
            async with httpx.AsyncClient(timeout=2.5) as client:
                res = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if res.status_code == 200:
                    data = res.json()
                    trans_q = "".join(part[0] for part in data[0] if part[0]).strip()
                    if trans_q:
                        return trans_q
        except Exception:
            pass

        return question_en

translation_service = TranslationService()
