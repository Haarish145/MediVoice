import logging
import re
import urllib.parse
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("medivoice.translation")

# Rich offline medical translation dictionary for Indian languages
INDIC_NUMERAL_MAP = {
    # Devanagari (Hindi, Marathi)
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    # Bengali / Assamese
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
    # Gurmukhi (Punjabi)
    '੦': '0', '੧': '1', '੨': '2', '੩': '3', '੪': '4', '੫': '5', '੬': '6', '੭': '7', '੮': '8', '੯': '9',
    # Gujarati
    '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4', '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9',
    # Odia
    '୦': '0', '୧': '1', '୨': '2', '୩': '3', '୪': '4', '୫': '5', '୬': '6', '୭': '7', '୮': '8', '୯': '9',
    # Tamil
    '௧': '1', '௨': '2', '௩': '3', '௪': '4', '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9', '௰': '10',
    # Telugu
    '౦': '0', '౧': '1', '౨': '2', '౩': '3', '౪': '4', '౫': '5', '౬': '6', '౭': '7', '౮': '8', '౯': '9',
    # Kannada
    '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4', '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9',
    # Malayalam
    '൦': '0', '൧': '1', '൨': '2', '൩': '3', '൪': '4', '൫': '5', '൬': '6', '൭': '7', '൮': '8', '൯': '9',
}

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
        "10 நிமிடங்கள்": "10 minutes",
        "15 நிமிடங்கள்": "15 minutes",
        "30 நிமிடங்கள்": "30 minutes",
        "1 மணி நேரம்": "1 hour",
        "2 மணி நேரம்": "2 hours",
        "ஒரு மணி நேரம்": "1 hour",
        "இரண்டு மணி நேரம்": "2 hours",
        "5 நிமிடங்களாக": "for 5 minutes",
        "20 நிமிடங்களாக": "for 20 minutes",
        "நேற்று முதல்": "since yesterday",
        "காலையிலிருந்து": "since morning",
        "மூச்சு விடுவதில் சிரமமாக இருக்கிறது": "I am having difficulty breathing.",
        "மூச்சு விடுவதில் சிரமம்": "Difficulty breathing",
        "மூச்சு திணறல்": "Shortness of breath",
        "காய்ச்சல் மற்றும் தலைவலி": "Fever and headache",
        "காய்ச்சல்": "Fever",
        "தலைவலி": "Headache",
        "வயிறு வலி": "Abdominal pain",
        "முதுகு வலி": "Back pain",
        "இருமல்": "Cough",
        "வாந்தி": "Vomiting",
        "மயக்கம்": "Dizziness",
        "திடீரென்று": "suddenly",
        "மிகவும் அதிகம்": "very severe",
        "தாங்க முடியவில்லை": "unbearable",
        "லேசான வலி": "mild pain",
        "மிதமான வலி": "moderate pain",
        "இல்லை": "No, no other problem.",
        "வேறு பிரச்சனை இல்லை": "No other problems.",
        "முடித்துக் கொள்ளலாம்": "We can complete the session.",
        "வேறொன்றுமில்லை": "Nothing else.",
        "ஒன்று": "1", "இரண்டு": "2", "மூன்று": "3", "நான்கு": "4", "ஐந்து": "5",
        "ஆறு": "6", "ஏழு": "7", "எட்டு": "8", "ஒன்பது": "9", "பத்து": "10"
    },
    "hi": {
        "मुझे अचानक सीने में दर्द हुआ": "I suddenly developed chest pain.",
        "मुझे सीने में दर्द है": "I have chest pain.",
        "सीने में दर्द": "Chest pain",
        "20 मिनट से": "For 20 minutes",
        "5 मिनट से": "For 5 minutes",
        "20 मिनट": "20 minutes",
        "5 मिनट": "5 minutes",
        "10 मिनट": "10 minutes",
        "15 मिनट": "15 minutes",
        "30 मिनट": "30 minutes",
        "1 घंटा": "1 hour",
        "2 घंटे": "2 hours",
        "दो घंटे": "2 hours",
        "एक घंटा": "1 hour",
        "कल से": "since yesterday",
        "सुबह से": "since morning",
        "दो दिन से": "for two days",
        "मुझे सांस लेने में तकलीफ हो रही है": "I am having difficulty breathing.",
        "सांस लेने में तकलीफ": "Difficulty breathing",
        "मुझे बुखार और सिरदर्द है": "I have fever and headache",
        "बुखार": "Fever",
        "सिरदर्द": "Headache",
        "पेट दर्द": "Abdominal pain",
        "कमर दर्द": "Back pain",
        "खांसी": "Cough",
        "उल्टी": "Vomiting",
        "चक्कर": "Dizziness",
        "अचानक": "suddenly",
        "बहुत तेज": "very severe",
        "नहीं": "No, no other problem.",
        "और कुछ नहीं": "Nothing else.",
        "पूरा कर सकते हैं": "We can complete the session.",
        "एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पांच": "5",
        "छह": "6", "सात": "7", "आठ": "8", "नौ": "9", "दस": "10"
    },
    "te": {
        "నాకు ఛాతీలో నొప్పిగా ఉంది": "I have chest pain.",
        "ఛాతీ నొప్పి": "Chest pain",
        "శ్వాస తీసుకోవడంలో ఇబ్బంది": "Difficulty breathing",
        "జ్వరం": "Fever",
        "తలనొప్పి": "Headache",
        "కడుపు నొప్పి": "Abdominal pain",
        "దగ్గు": "Cough",
        "వాంతులు": "Vomiting",
        "కళ్ళు తిరగడం": "Dizziness",
        "5 నిమిషాలు": "5 minutes",
        "20 నిమిషాలు": "20 minutes",
        "రెండు గంటలు": "2 hours",
        "నిన్నటి నుండి": "since yesterday",
        "ఉదయం నుండి": "since morning",
        "లేదు": "No other problem.",
        "ఒకటి": "1", "రెండు": "2", "మూడు": "3", "నాలుగు": "4", "ఐదు": "5",
        "ఆరు": "6", "ఏడు": "7", "ఎనిమిది": "8", "తొమ్మిది": "9", "పది": "10"
    },
    "kn": {
        "ನನಗೆ ಎದೆ ನೋವು ಇದೆ": "I have chest pain.",
        "ಎದೆ ನೋವು": "Chest pain",
        "ಉಸಿರಾಟದ ತೊಂದರೆ": "Difficulty breathing",
        "ಜ್ವರ": "Fever",
        "ತಲೆನೋವು": "Headache",
        "ಹೊಟ್ಟೆ ನೋವು": "Abdominal pain",
        "ಕೆಮ್ಮು": "Cough",
        "ವಾಂತಿ": "Vomiting",
        "ತಲೆಸುತ್ತು": "Dizziness",
        "5 ನಿಮಿಷಗಳು": "5 minutes",
        "20 ನಿಮಿಷಗಳು": "20 minutes",
        "ಎರಡು ಗಂಟೆಗಳು": "2 hours",
        "ನಿನ್ನೆಯಿಂದ": "since yesterday",
        "ಬೆಳಿಗ್ಗೆಯಿಂದ": "since morning",
        "ಇಲ್ಲ": "No other problem.",
        "ಒಂದು": "1", "ಎರಡು": "2", "ಮೂರು": "3", "ನಾಲ್ಕು": "4", "ಐದು": "5",
        "ಆರು": "6", "ಏಳು": "7", "ಎಂಟು": "8", "ಒಂಬತ್ತು": "9", "ಹತ್ತು": "10"
    },
    "ml": {
        "എനിക്ക് നെഞ്ചുവേദനയുണ്ട്": "I have chest pain.",
        "നെഞ്ചുവേദന": "Chest pain",
        "ശ്വാസതടസ്സം": "Difficulty breathing",
        "പനി": "Fever",
        "തലവേദന": "Headache",
        "വയറുവേദന": "Abdominal pain",
        "ചുമ": "Cough",
        "ഛർദ്ദി": "Vomiting",
        "തലകറക്കം": "Dizziness",
        "5 മിനിറ്റ്": "5 minutes",
        "20 മിനിറ്റ്": "20 minutes",
        "രണ്ട് മണിക്കൂർ": "2 hours",
        "ഇന്നലെ മുതൽ": "since yesterday",
        "രാവിലെ മുതൽ": "since morning",
        "ഇല്ല": "No other problem.",
        "ഒന്ന്": "1", "രണ്ട്": "2", "മൂന്ന്": "3", "നാല്": "4", "അഞ്ച്": "5",
        "ആറ്": "6", "ഏഴ്": "7", "എട്ട്": "8", "ഒമ്പത്": "9", "പത്ത്": "10"
    },
    "bn": {
        "আমার বুকে ব্যথা করছে": "I have chest pain.",
        "বুকে ব্যথা": "Chest pain",
        "শ্বাসকষ্ট": "Difficulty breathing",
        "জ্বর": "Fever",
        "মাথাব্যথা": "Headache",
        "পেটে ব্যথা": "Abdominal pain",
        "কাশি": "Cough",
        "বমি": "Vomiting",
        "মাথা ঘোরা": "Dizziness",
        "৫ মিনিট": "5 minutes",
        "২০ মিনিট": "20 minutes",
        "২ ঘন্টা": "2 hours",
        "গতকাল থেকে": "since yesterday",
        "সকাল থেকে": "since morning",
        "না": "No other problem.",
        "এক": "1", "দুই": "2", "তিন": "3", "চার": "4", "পাঁচ": "5",
        "ছয়": "6", "সাত": "7", "আট": "8", "নয়": "9", "দশ": "10"
    },
    "mr": {
        "माझ्या छातीत दुखत आहे": "I have chest pain.",
        "छातीत दुखणे": "Chest pain",
        "श्वास घेण्यास त्रास": "Difficulty breathing",
        "ताप": "Fever",
        "डोकेदुखी": "Headache",
        "पोटदुखी": "Abdominal pain",
        "खोकला": "Cough",
        "उलटी": "Vomiting",
        "चक्कर येणे": "Dizziness",
        "५ मिनिटे": "5 minutes",
        "२० मिनिटे": "20 minutes",
        "२ तास": "2 hours",
        "कालपासून": "since yesterday",
        "सकाळपासून": "since morning",
        "नाही": "No other problem.",
        "एक": "1", "दोन": "2", "तीन": "3", "चार": "4", "पाच": "5",
        "सहा": "6", "सात": "7", "आठ": "8", "नऊ": "9", "दहा": "10"
    },
    "gu": {
        "મને છાતીમાં દુખાવો થાય છે": "I have chest pain.",
        "છાતીમાં દુખાવો": "Chest pain",
        "શ્વાસ લેવામાં તકલીફ": "Difficulty breathing",
        "તાવ": "Fever",
        "માથાનો દુખાવો": "Headache",
        "પેટમાં દુખાવો": "Abdominal pain",
        "ઉધરસ": "Cough",
        "ઉલટી": "Vomiting",
        "ચક્કર": "Dizziness",
        "૫ મિનિટ": "5 minutes",
        "૨૦ મિનિટ": "20 minutes",
        "૨ કલાક": "2 hours",
        "ગઈકાલથી": "since yesterday",
        "સવારથી": "since morning",
        "ના": "No other problem.",
        "એક": "1", "બે": "2", "ત્રણ": "3", "ચાર": "4", "પાંચ": "5",
        "છ": "6", "સાત": "7", "આઠ": "8", "નવ": "9", "દસ": "10"
    },
    "pa": {
        "ਮੇਰੀ ਛਾਤੀ ਵਿੱਚ ਦਰਦ ਹੈ": "I have chest pain.",
        "ਛਾਤੀ ਦਾ ਦਰਦ": "Chest pain",
        "ਸਾਹ ਲੈਣ ਵਿੱਚ ਤਕਲੀਫ": "Difficulty breathing",
        "ਬੁਖਾਰ": "Fever",
        "ਸਿਰਦਰਦ": "Headache",
        "ਪੇਟ ਦਰਦ": "Abdominal pain",
        "ਖੰਘ": "Cough",
        "ਉਲਟੀ": "Vomiting",
        "ਚੱਕਰ ਆਉਣਾ": "Dizziness",
        "ਨਹੀਂ": "No other problem."
    },
    "or": {
        "ମୋ ଛାତିରେ ଯନ୍ତ୍ରଣା ହେଉଛି": "I have chest pain.",
        "ଛାତି ଯନ୍ତ୍ରଣା": "Chest pain",
        "ନିଶ୍ୱାସ ନେବାରେ କଷ୍ଟ": "Difficulty breathing",
        "ଜ୍ୱର": "Fever",
        "ମୁଣ୍ଡବିନ୍ଧା": "Headache",
        "ପେଟ ଯନ୍ତ୍ରଣା": "Abdominal pain",
        "ନାହିଁ": "No other problem."
    },
    "as": {
        "মোৰ বুকুত বিষ হৈছে": "I have chest pain.",
        "বুকুৰ বিষ": "Chest pain",
        "উশাহ লোৱাত কষ্ট": "Difficulty breathing",
        "জ্বৰ": "Fever",
        "মূৰৰ বিষ": "Headache",
        "পেটৰ বিষ": "Abdominal pain",
        "নহয়": "No other problem."
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
    (re.compile(r"முதுகு\s*வலி", re.IGNORECASE), "back pain"),
    (re.compile(r"இருமல்", re.IGNORECASE), "cough"),
    (re.compile(r"வாந்தி", re.IGNORECASE), "vomiting"),
    (re.compile(r"மயக்கம்", re.IGNORECASE), "dizziness"),
    (re.compile(r"திடீரென்று|திடீரென", re.IGNORECASE), "suddenly"),
    (re.compile(r"(\d+)\s*நிமிட(?:ங்கள்|ங்களாக|மாக)", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*மணி\s*நேர(?:ங்கள்|மாக)", re.IGNORECASE), r"\1 hours"),
    (re.compile(r"(\d+)\s*நா(?:ட்கள்|ளாக|ளாய்)", re.IGNORECASE), r"\1 days"),
    (re.compile(r"எனக்கு", re.IGNORECASE), "I have"),
    (re.compile(r"இருக்கிறது|உள்ளது|வலிக்குது", re.IGNORECASE), ""),
    # Hindi
    (re.compile(r"सीने\s*में\s*दर्द", re.IGNORECASE), "chest pain"),
    (re.compile(r"सांस\s*(?:लेने\s*में\s*तकलीफ|फूलना)", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"सिर\s*दर्द", re.IGNORECASE), "headache"),
    (re.compile(r"पेट\s*दर्द", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"कमर\s*दर्द|पीठ\s*दर्द", re.IGNORECASE), "back pain"),
    (re.compile(r"बुखार", re.IGNORECASE), "fever"),
    (re.compile(r"खांसी", re.IGNORECASE), "cough"),
    (re.compile(r"उल्टी", re.IGNORECASE), "vomiting"),
    (re.compile(r"चक्कर", re.IGNORECASE), "dizziness"),
    (re.compile(r"अचानक", re.IGNORECASE), "suddenly"),
    (re.compile(r"(\d+)\s*मिनट", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*घंटे?", re.IGNORECASE), r"\1 hours"),
    (re.compile(r"(\d+)\s*दिन", re.IGNORECASE), r"\1 days"),
    (re.compile(r"मुझे", re.IGNORECASE), "I have"),
    (re.compile(r"हो\s*रहा\s*है|है", re.IGNORECASE), ""),
    # Telugu
    (re.compile(r"ఛాతీ(?:లో)?\s*నొప్పి", re.IGNORECASE), "chest pain"),
    (re.compile(r"శ్వాస\s*(?:తీసుకోవడంలో\s*)?ఇబ్బంది", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"తలనొప్పి", re.IGNORECASE), "headache"),
    (re.compile(r"కడుపు\s*నొప్పి", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"జ్వరం", re.IGNORECASE), "fever"),
    (re.compile(r"(\d+)\s*నిమిషాలు", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*గంటలు", re.IGNORECASE), r"\1 hours"),
    (re.compile(r"(\d+)\s*రోజులు", re.IGNORECASE), r"\1 days"),
    # Kannada
    (re.compile(r"ಎದೆ\s*ನೋವು", re.IGNORECASE), "chest pain"),
    (re.compile(r"ಉಸಿರಾಟದ\s*ತೊಂದರೆ", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"ತಲೆನೋವು", re.IGNORECASE), "headache"),
    (re.compile(r"ಹೊಟ್ಟೆ\s*ನೋವು", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"ಜ್ವರ", re.IGNORECASE), "fever"),
    (re.compile(r"(\d+)\s*ನಿಮಿಷಗಳು", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*ಗಂಟೆಗಳು", re.IGNORECASE), r"\1 hours"),
    # Malayalam
    (re.compile(r"നെഞ്ചുവേദന", re.IGNORECASE), "chest pain"),
    (re.compile(r"ശ്വാസതടസ്സം", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"തലവേദന", re.IGNORECASE), "headache"),
    (re.compile(r"വയറുവേദന", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"പനി", re.IGNORECASE), "fever"),
    (re.compile(r"(\d+)\s*മിനിറ്റ്", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*മണിക്കൂർ", re.IGNORECASE), r"\1 hours"),
    # Bengali
    (re.compile(r"বুকে\s*ব্যথা", re.IGNORECASE), "chest pain"),
    (re.compile(r"শ্বাসকষ্ট", re.IGNORECASE), "difficulty breathing"),
    (re.compile(r"মাথাব্যথা", re.IGNORECASE), "headache"),
    (re.compile(r"পেটে\s*ব্যথা", re.IGNORECASE), "abdominal pain"),
    (re.compile(r"জ্বর", re.IGNORECASE), "fever"),
    (re.compile(r"(\d+)\s*মিনিট", re.IGNORECASE), r"\1 minutes"),
    (re.compile(r"(\d+)\s*ঘন্টা", re.IGNORECASE), r"\1 hours"),
]

QUESTION_TRANSLATIONS = {
    "ta": {
        "duration": "இந்த வலி எவ்வளவு நேரமாக இருக்கிறது?",
        "severity": "இந்த வலி எவ்வளவு கடுமையாக இருக்கிறது (1 முதல் 10 வரை)?",
        "breathing": "மூச்சு விடுவதில் சிரமம் உள்ளதா?",
        "breathing_difficulty": "மூச்சு விடுவதில் சிரமம் உள்ளதா?",
        "onset": "இந்த வலி திடீரென வந்ததா அல்லது மெதுவாகத் தொடங்கியதா?",
        "additional_symptoms_prompt": "உங்களுக்கு உள்ள மற்ற அறிகுறிகள் அல்லது பிரச்சனைகள் பற்றி சொல்லுங்கள்.",
        "additional_duration": "இந்த பிரச்சனை எவ்வளவு நேரமாக இருக்கிறது?",
        "additional_severity": "இந்த பிரச்சனை எவ்வளவு கடுமையாக இருக்கிறது (1 முதல் 10 வரை)?",
        "completion_check": "உங்களுக்கு வேறு ஏதேனும் உடல்நலப் பிரச்சனை உள்ளதா, அல்லது இந்த பதிவை முடித்துக் கொள்ளலாமா?"
    },
    "hi": {
        "duration": "यह दर्द कितने समय से हो रहा है?",
        "severity": "यह दर्द कितना तेज है (1 से 10 के पैमाने पर)?",
        "breathing": "क्या आपको सांस लेने में तकलीफ हो रही है?",
        "breathing_difficulty": "क्या आपको सांस लेने में तकलीफ हो रही है?",
        "onset": "क्या यह दर्द अचानक शुरू हुआ?",
        "additional_symptoms_prompt": "कृपया बताएं कि आपको और क्या लक्षण या समस्याएं हो रही हैं।",
        "additional_duration": "यह समस्या कितने समय से हो रही है?",
        "additional_severity": "यह समस्या कितनी तेज है (1 से 10 के पैमाने पर)?",
        "completion_check": "क्या आपको कोई अन्य समस्या है, या हम सत्र पूरा कर सकते हैं?"
    },
    "te": {
        "duration": "ఈ నొప్పి ఎంత సమయం నుండి ఉంది?",
        "severity": "ఈ నొప్పి ఎంత తీవ్రంగా ఉంది (1 నుండి 10)?",
        "breathing": "శ్వాస తీసుకోవడంలో ఇబ్బంది ఉందా?",
        "breathing_difficulty": "శ్వాస తీసుకోవడంలో ఇబ్బంది ఉందా?",
        "onset": "ఈ నొప్పి హఠాత్తుగా మొదలైందా?",
        "additional_symptoms_prompt": "మీకు ఉన్న ఇతర లక్షణాలు లేదా సమస్యల గురించి దయచేసి చెప్పండి.",
        "additional_duration": "ఈ సమస్య ఎంత సమయం నుండి ఉంది?",
        "additional_severity": "ఈ సమస్య ఎంత తీవ్రంగా ఉంది (1 నుండి 10)?",
        "completion_check": "మీకు ఇతర సమస్యలు ఏమైనా ఉన్నాయా, లేదా సెషన్‌ను పూర్తి చేయవచ్చా?"
    },
    "kn": {
        "duration": "ಈ ನೋವು ಎಷ್ಟು ಸಮಯದಿಂದ ಇದೆ?",
        "severity": "ಈ ನೋವು ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ (1 ರಿಂದ 10)?",
        "breathing": "ಉಸಿರಾಟದಲ್ಲಿ ತೊಂದರೆ ಇದೆಯೇ?",
        "breathing_difficulty": "ಉಸಿರಾಟದಲ್ಲಿ ತೊಂದರೆ ಇದೆಯೇ?",
        "onset": "ಈ ನೋವು ಹಠಾತ್ತನೆ ಪ್ರಾರಂಭವಾಯಿತೇ?",
        "additional_symptoms_prompt": "ನೀವು ಅನುಭವಿಸುತ್ತಿರುವ ಇತರ ಲಕ್ಷಣಗಳು ಅಥವಾ ಸಮಸ್ಯೆಗಳ ಬಗ್ಗೆ ದಯವಿಟ್ಟು ಹೇಳಿ.",
        "additional_duration": "ಈ ಸಮಸ್ಯೆ ಎಷ್ಟು ಸಮಯದಿಂದ ಇದೆ?",
        "additional_severity": "ಈ ಸಮಸ್ಯೆ ಎಷ್ಟು ತೀವ್ರವಾಗಿದೆ (1 ರಿಂದ 10)?",
        "completion_check": "ನಿಮಗೆ ಬೇರೆ ಏನಾದರೂ ಸಮಸ್ಯೆ ಇದೆಯೇ, ಅಥವಾ ಅಧಿವೇಶನವನ್ನು ಪೂರ್ಣಗೊಳಿಸಬಹುದೇ?"
    },
    "ml": {
        "duration": "ഈ വേദന എത്ര സമയമായി ഉണ്ട്?",
        "severity": "വേദന എത്രത്തോളം കഠിനമാണ് (1 മുതൽ 10 വരെ)?",
        "breathing": "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ടുണ്ടോ?",
        "breathing_difficulty": "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ടുണ്ടോ?",
        "onset": "ഈ വേദന പെട്ടെന്ന് തുടങ്ങിയതാണോ?",
        "additional_symptoms_prompt": "നിങ്ങൾ അനുഭവിക്കുന്ന മറ്റ് ലക്ഷണങ്ങളെക്കുറിച്ചോ പ്രശ്നങ്ങളെക്കുറിച്ചോ പറയൂ.",
        "additional_duration": "ഈ പ്രശ്നം എത്ര സമയമായി ഉണ്ട്?",
        "additional_severity": "ഈ പ്രശ്നം എത്രത്തോളം കഠിനമാണ് (1 മുതൽ 10 വരെ)?",
        "completion_check": "നിങ്ങൾക്ക് മറ്റ് എന്തെങ്കിലും പ്രശ്നങ്ങളുണ്ടോ, അല്ലെങ്കിൽ ഈ സെഷൻ പൂർത്തിയാക്കാമോ?"
    },
    "bn": {
        "duration": "এই ব্যথা কতক্ষণ ধরে হচ্ছে?",
        "severity": "এই ব্যথা কতটা তীব্র (১ থেকে ১০ এর মধ্যে)?",
        "breathing": "আপনার কি শ্বাস নিতে কষ্ট হচ্ছে?",
        "breathing_difficulty": "আপনার কি শ্বাস নিতে কষ্ট হচ্ছে?",
        "onset": "এই ব্যথা কি হঠাৎ শুরু হয়েছে?",
        "additional_symptoms_prompt": "আপনার আর কী কী লক্ষণ বা সমস্যা হচ্ছে তা বলুন।",
        "additional_duration": "এই সমস্যা কতক্ষণ ধরে হচ্ছে?",
        "additional_severity": "এই সমস্যা কতটা তীব্র (১ থেকে ১০)?",
        "completion_check": "আপনার কি আর কোনো সমস্যা আছে, নাকি আমরা সেশন শেষ করতে পারি?"
    },
    "mr": {
        "duration": "हे दुखणे किती वेळापासून आहे?",
        "severity": "हे दुखणे किती तीव्र आहे (१ ते १० पैकी)?",
        "breathing": "तुम्हाला श्वास घेण्यास त्रास होतो आहे का?",
        "breathing_difficulty": "तुम्हाला श्वास घेण्यास त्रास होतो आहे का?",
        "onset": "हे दुखणे अचानक सुरू झाले का?",
        "additional_symptoms_prompt": "तुम्हाला इतर कोणती लक्षणे किंवा त्रास होत आहेत ते सांगा.",
        "additional_duration": "ही समस्या किती वेळापासून आहे?",
        "additional_severity": "ही समस्या किती तीव्र आहे (१ ते १० पैकी)?",
        "completion_check": "तुम्हाला आणखी काही त्रास आहे का, किंवा आपण सत्र पूर्ण करू शकतो का?"
    },
    "gu": {
        "duration": "આ દુખાવો કેટલા સમયથી છે?",
        "severity": "આ દુખાવો કેટલો તીવ્ર છે (૧ થી ૧૦ સ્કેલ પર)?",
        "breathing": "શ્વાસ લેવામાં તકલીફ થઈ રહી છે?",
        "breathing_difficulty": "શ્વાસ લેવામાં તકલીફ થઈ રહી છે?",
        "onset": "આ દુખાવો અચાનક શરૂ થયો?",
        "additional_symptoms_prompt": "તમને અન્ય કયા લક્ષણો કે તકલીફો થઈ રહી છે તે જણાવો.",
        "additional_duration": "આ સમસ્યા કેટલા સમયથી છે?",
        "additional_severity": "આ સમસ્યા કેટલી તીવ્ર છે (૧ થી ૧૦)?",
        "completion_check": "તમને બીજી કોઈ તકલીફ છે, અથવા આપણે સત્ર પૂર્ણ કરી શકીએ?"
    },
    "pa": {
        "duration": "ਇਹ ਦਰਦ ਕਿੰਨੇ ਸਮੇਂ ਤੋਂ ਹੈ?",
        "severity": "ਇਹ ਦਰਦ ਕਿੰਨਾ ਗੰਭੀਰ ਹੈ (1 ਤੋਂ 10)?",
        "breathing": "ਕੀ ਤੁਹਾਨੂੰ ਸਾਹ ਲੈਣ ਵਿੱਚ ਮੁਸ਼ਕਲ ਹੋ ਰਹੀ ਹੈ?",
        "breathing_difficulty": "ਕੀ ਤੁਹਾਨੂੰ ਸਾਹ ਲੈਣ ਵਿੱਚ ਮੁਸ਼ਕਲ ਹੋ ਰਹੀ ਹੈ?",
        "onset": "ਕੀ ਇਹ ਦਰਦ ਅਚਾਨਕ ਸ਼ੁਰੂ ਹੋਇਆ?",
        "additional_symptoms_prompt": "ਕਿਰਪਾ ਕਰਕੇ ਦੱਸੋ ਕਿ ਤੁਹਾਨੂੰ ਹੋਰ ਕਿਹੜੇ ਲੱਛਣ ਜਾਂ ਸਮੱਸਿਆਵਾਂ ਹੋ ਰਹੀਆਂ ਹਨ।",
        "additional_duration": "ਇਹ ਸਮੱਸਿਆ ਕਿੰਨੇ ਸਮੇਂ ਤੋਂ ਹੈ?",
        "additional_severity": "ਇਹ ਸਮੱਸਿਆ ਕਿੰਨੀ ਗੰਭੀਰ ਹੈ (1 ਤੋਂ 10)?",
        "completion_check": "ਕੀ ਤੁਹਾਡੀ ਕੋਈ ਹੋਰ ਸਮੱਸਿਆ ਹੈ, ਜਾਂ ਅਸੀਂ ਸੈਸ਼ਨ ਪੂਰਾ ਕਰ ਸਕਦੇ ਹਾਂ?"
    },
    "or": {
        "duration": "ଏହି ଯନ୍ତ୍ରଣା କେତେ ସମୟ ଧରି ଅଛି?",
        "severity": "ଏହି ଯନ୍ତ୍ରଣା କେତେ ତୀବ୍ର (୧ ରୁ ୧୦)?",
        "breathing": "ଆପଣଙ୍କୁ ନିଶ୍ୱାସ ନେବାରେ ଅସୁବିଧା ହଉଛି କି?",
        "breathing_difficulty": "ଆପଣଙ୍କୁ ନିଶ୍ୱାସ ନେବାରେ ଅସୁବିଧା ହଉଛି କି?",
        "onset": "ଏହି ଯନ୍ତ୍ରଣା ହଠାତ୍ ଆରମ୍ଭ ହୋଇଥିଲା?",
        "additional_symptoms_prompt": "ଆପଣଙ୍କର ଆଉ କ'ଣ ଲକ୍ଷଣ ବା ସମସ୍ୟା ଅଛି କୁହନ୍ତୁ।",
        "additional_duration": "ଏହି ସମସ୍ୟା କେତେ ସମୟ ଧରି ଅଛି?",
        "additional_severity": "ଏହି ସମସ୍ୟା କେତେ ତୀବ୍ର (୧ ରୁ ୧୦)?",
        "completion_check": "ଆପଣଙ୍କର ଆଉ କୌଣସି ସମସ୍ୟା ଅଛି, ନଥିଲେ ଆମେ ସଂଶୋଧନ ସଂପୂର୍ଣ୍ଣ କରିପାରିବା?"
    },
    "as": {
        "duration": "এই বিষ কিমান সময়ৰ পৰা হৈছে?",
        "severity": "এই বিষ কিমান তীব্ৰ (১ ৰ পৰা ১০)?",
        "breathing": "আপোনাৰ উশাহ লোৱাত অসুবিধা হৈছে নেকি?",
        "breathing_difficulty": "আপোনাৰ উশাহ লোৱাত অসুবিধা হৈছে নেকি?",
        "onset": "এই বিষ হঠাতে আৰম্ভ হৈছিল নেকি?",
        "additional_symptoms_prompt": "আপোনাৰ আৰু কি লক্ষণ বা সমস্যা হৈছে কওক।",
        "additional_duration": "এই সমস্যা কিমান সময়ৰ পৰা হৈছে?",
        "additional_severity": "এই সমস্যা কিমান তীব্ৰ (১ ৰ পৰা ১০)?",
        "completion_check": "আপোনাৰ আৰু কোনো সমস্যা আছে নেকি, নহলে আমি অধিবেশন সম্পূৰ্ণ কৰিব পাৰো?"
    },
    "en": {
        "duration": "How long have you been experiencing these symptoms?",
        "severity": "How severe is your discomfort on a scale of 1 to 10?",
        "breathing": "Are you experiencing any difficulty breathing or shortness of breath?",
        "breathing_difficulty": "Are you experiencing any difficulty breathing or shortness of breath?",
        "onset": "Did these symptoms start suddenly or gradually?",
        "additional_symptoms_prompt": "Please describe what other symptoms or problems you are experiencing.",
        "additional_duration": "How long have you been experiencing this problem?",
        "additional_severity": "How severe is this problem on a scale of 1 to 10?",
        "completion_check": "Do you have any other symptoms or problems, or can we complete the intake session?"
    }
}


ADDITIONAL_SYMPTOMS_PROMPT = {
    'ta': 'உங்களுக்கு உள்ள மற்ற அறிகுறிகள் அல்லது பிரச்சனைகள் பற்றி சொல்லுங்கள்.',
    'hi': 'कृपया बताएं कि आपको और क्या लक्षण या समस्याएं हो रही हैं।',
    'te': 'మీకు ఉన్న ఇతర లక్షణాలు లేదా సమస్యల గురించి దయచేసి చెప్పండి.',
    'kn': 'ನೀವು ಅನುಭವಿಸುತ್ತಿರುವ ಇತರ ಲಕ್ಷಣಗಳು ಅಥವಾ ಸಮಸ್ಯೆಗಳ ಬಗ್ಗೆ ದಯವಿಟ್ಟು ಹೇಳಿ.',
    'ml': 'നിങ്ങൾ അനുഭവിക്കുന്ന മറ്റ് ലക്ഷണങ്ങളെക്കുറിച്ചോ പ്രശ്നങ്ങളെക്കുറിച്ചോ പറയൂ.',
    'bn': 'আপনার আর কী কী লক্ষণ বা সমস্যা হচ্ছে তা বলুন।',
    'mr': 'तुम्हाला इतर कोणती लक्षणे किंवा त्रास होत आहेत ते सांगा.',
    'gu': 'તમને અન્ય કયા લક્ષણો કે તકલીફો થઈ રહી છે તે જણાવો.',
    'pa': 'ਕਿਰਪਾ ਕਰਕੇ ਦੱਸੋ ਕਿ ਤੁਹਾਨੂੰ ਹੋਰ ਕਿਹੜੇ ਲੱਛਣ ਜਾਂ ਸਮੱਸਿਆਵਾਂ ਹੋ ਰਹੀਆਂ ਹਨ।',
    'or': 'ଆପଣଙ୍କର ଆଉ କ’ଣ ଲକ୍ଷଣ ବା ସମସ୍ୟା ଅଛି କୁହନ୍ତୁ।',
    'as': 'আপোনাৰ আৰু কি লক্ষণ বা সমস্যা হৈছে কওক।',
    'en': 'Please describe what other symptoms or problems you are experiencing.'
}

for _lang, _text in ADDITIONAL_SYMPTOMS_PROMPT.items():
    if _lang in QUESTION_TRANSLATIONS:
        QUESTION_TRANSLATIONS[_lang]['additional_symptoms_prompt'] = _text

def remove_non_latin(text: str) -> str:
    """Removes non-Latin characters leaving only English text, numbers and punctuation."""
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()

class TranslationService:
    async def _online_translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        if not text or not text.strip():
            return ""
        
        sl = source_lang if source_lang else "auto"
        tl = target_lang
        quoted = urllib.parse.quote(text.strip())
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }

        # 1. Primary: Google Client Chrome Extension endpoint (Extremely reliable, not throttled)
        try:
            url1 = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={sl}&tl={tl}&q={quoted}"
            async with httpx.AsyncClient(timeout=3.5) as client:
                res = await client.get(url1, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        parts = []
                        for item in data:
                            if isinstance(item, str):
                                parts.append(item)
                            elif isinstance(item, list) and len(item) > 0 and isinstance(item[0], str):
                                parts.append(item[0])
                        result = " ".join(parts).strip()
                        if result:
                            return result
                    elif isinstance(data, str) and data.strip():
                        return data.strip()
        except Exception as e:
            logger.debug(f"Chrome-ex translate failed: {e}")

        # 2. Secondary: MyMemory Translation API
        try:
            pair = f"{sl}|{tl}"
            url2 = f"https://api.mymemory.translated.net/get?q={quoted}&langpair={pair}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url2, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    trans = data.get("responseData", {}).get("translatedText", "").strip()
                    if trans and not trans.startswith("MYMEMORY WARNING:") and "INVALID" not in trans.upper():
                        return trans
        except Exception as e:
            logger.debug(f"MyMemory translate failed: {e}")

        # 3. Tertiary: Google GTX public endpoint
        try:
            url3 = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={quoted}"
            async with httpx.AsyncClient(timeout=2.5) as client:
                res = await client.get(url3, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    trans = "".join(part[0] for part in data[0] if part and part[0]).strip()
                    if trans:
                        return trans
        except Exception as e:
            logger.debug(f"Google GTX translate failed: {e}")

        return None

    async def translate_to_english(self, text: str, source_language: str = "ta") -> str:
        if not text or not text.strip():
            return ""
            
        stripped = text.strip()
        
        # If source language is already English and text is purely ASCII
        if source_language == "en" and all(ord(c) < 128 for c in stripped):
            return stripped

        # Normalize Indic numerals
        normalized = stripped
        for ind_d, asc_d in INDIC_NUMERAL_MAP.items():
            normalized = normalized.replace(ind_d, asc_d)

        # Standalone numbers (e.g. "8", "8/10", "10")
        if re.match(r"^\s*([1-9]|10)\s*$", normalized):
            return normalized.strip()

        # 1. Exact match in offline dictionary
        lang_dict = COMMON_TRANSLATIONS.get(source_language, {})
        if stripped in lang_dict:
            return lang_dict[stripped]
        if normalized in lang_dict:
            return lang_dict[normalized]

        # 2. Try Online High-Accuracy Multi-Tier Translation
        online_res = await self._online_translate(normalized, source_language, "en")
        if online_res:
            cleaned = remove_non_latin(online_res)
            if cleaned:
                return cleaned
            return online_res

        # 3. Offline heuristic / phrase substitution fallback
        working = normalized
        for pattern, replacement in PHRASE_REPLACEMENTS:
            working = pattern.sub(replacement, working)

        cleaned = remove_non_latin(working)
        if cleaned and len(cleaned) > 1:
            return cleaned

        # 4. Check if digits exist in input (e.g. duration or scale rating)
        digits = re.findall(r"\b\d+\b", normalized)
        if digits:
            return " ".join(digits)

        # 5. Fallback: Return original input cleanly rather than fake "Patient reports acute symptoms"
        return stripped

    async def translate_question(self, question_en: str, target_language: str, question_type: str = "") -> str:
        if target_language == "en":
            return question_en
            
        lang_questions = QUESTION_TRANSLATIONS.get(target_language, {})
        if question_type in lang_questions:
            return lang_questions[question_type]
            
        # Try online translation with robust multi-tiered endpoints
        online_q = await self._online_translate(question_en, "en", target_language)
        if online_q:
            return online_q

        return question_en

translation_service = TranslationService()
