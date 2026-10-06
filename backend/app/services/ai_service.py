import logging
import re
from typing import Dict, Any, List
from app.schemas.ai import AIStructuredExtraction

logger = logging.getLogger("medivoice.ai")

class AIService:
    """
    Clinical Information Extraction Service.
    Extracts structured clinical information (complaint, symptoms, duration,
    severity, onset, location, red flags) strictly in canonical clinical English.
    """
    async def extract_triage_info(self, text: str, current_language: str = "en") -> AIStructuredExtraction:
        if not text:
            return AIStructuredExtraction()

        text_lower = text.lower()
        extracted = AIStructuredExtraction()

        def is_negated(keywords):
            for kw in keywords:
                pat = rf"\b(?:no|not|without|denies|negative for|don't have|dont have|no difficulty in|no difficulty with|no signs of)\s+(?:\w+\s+)?{re.escape(kw)}"
                if re.search(pat, text_lower):
                    return True
                if re.search(rf"\bno\s+.*{re.escape(kw)}", text_lower) and len(text_lower.split()) < 7:
                    return True
                if any(neg in text_lower for neg in ["இல்லை", "சிரமம் இல்லை", "இல்ல", "नहीं", "లేదు", "ಇಲ್ಲ"]):
                    return True
            return False

        # If input is clearly saying no more problems / completion, do not extract phantom symptoms
        is_pure_completion_or_negative = bool(re.search(
            r"\b(no other|no problem|no more|nothing else|finish|complete|that's all|thats all|all good|let's finish|lets finish|done|we can finish|we can complete)\b",
            text_lower
        )) or text_lower.strip() in ["no", "none", "nothing", "fine", "ok", "okay", "illai", "nahi"]

        if is_pure_completion_or_negative and not any(kw in text_lower for kw in ["also", "and i have", "still have", "pain", "fever", "cough", "ache"]):
            return extracted

        # 1. Main Complaint & Symptoms Extraction (Canonical English)
        if any(w in text_lower for w in ["chest pain", "chest discomfort", "angina", "tightness in chest", "pressure in chest", "மார்பில் வலி", "நெஞ்சு வலி", "சீனே"]) and not is_negated(["chest pain", "chest discomfort", "angina"]):
            extracted.main_complaint = "chest discomfort"
            extracted.symptoms.append("chest discomfort")
            extracted.location = "chest"
        elif any(w in text_lower for w in ["breath", "breathing difficulty", "shortness of breath", "dyspnea", "suffocat", "gasp", "மூச்சு"]) and not is_negated(["breath", "breathing difficulty", "shortness of breath", "dyspnea"]):
            extracted.main_complaint = "breathing difficulty"
            extracted.symptoms.append("breathing difficulty")
        elif any(w in text_lower for w in [
            "diarrhea", "diarrhoea", "loose motion", "loose motions", "food poisoning",
            "gastroenteritis", "stomach infection", "வயிற்றுப்போக்கு", "வயறறபபகக",
            "பேதி", "दस्त", "झाड़ा", "ଝାଡ଼ା", "ઝાડા", "విరేచనాలు"
        ]) and not is_negated(["diarrhea", "diarrhoea", "loose motion"]):
            is_sev = any(sw in text_lower for sw in ["severe", "acute", "heavy", "profuse", "10", "தீவிரமான", "கடுமையான", "तेज"])
            extracted.main_complaint = "severe diarrhea" if is_sev else "diarrhea"
            extracted.symptoms.append(extracted.main_complaint)
            extracted.location = "abdomen"
        elif any(w in text_lower for w in [
            "abdominal pain", "stomach pain", "stomach ache", "belly", "stomach",
            "வயிறு வலி", "வயிற்று வலி", "வயிற்றில் வலி", "வயறற வல", "வயிறு", "வயறற",
            "पेट दर्द", "पेट में दर्द", "కడుపు నొప్పి", "ಹೊಟ್ಟೆ ನೋವು", "cramp"
        ]) and not is_negated(["abdominal pain", "stomach pain", "belly"]):
            is_sev = any(sw in text_lower for sw in ["severe", "acute", "sharp", "terrible", "bad", "10", "தீவிரமான", "கடுமையான", "तेज"])
            extracted.main_complaint = "severe abdominal pain" if is_sev else "abdominal pain"
            extracted.symptoms.append(extracted.main_complaint)
            extracted.location = "abdomen"
        elif any(w in text_lower for w in ["headache", "head pain", "migraine", "தலைவலி", "सिरदर्द"]) and not is_negated(["headache", "head pain"]):
            extracted.main_complaint = "headache"
            extracted.symptoms.append("headache")
            extracted.location = "head"
        elif any(w in text_lower for w in ["stroke", "slurred speech", "facial drooping", "paralysis", "பக்கவாதம்", "लकवा"]) and not is_negated(["stroke", "slurred speech"]):
            extracted.main_complaint = "stroke symptoms"
            extracted.symptoms.append("slurred speech")
        elif any(w in text_lower for w in ["bleed", "hemorrhage", "blood", "ரத்தப்போக்கு", "रक्तस्राव"]) and not is_negated(["bleed", "blood"]):
            extracted.main_complaint = "acute bleeding"
            extracted.symptoms.append("acute bleeding")
        elif any(w in text_lower for w in ["fever", "chills", "high temperature", "காய்ச்சல்", "बुखार"]) and not is_negated(["fever", "chills"]):
            extracted.main_complaint = "fever"
            extracted.symptoms.append("fever")
        elif any(w in text_lower for w in ["cough", "cold", "sore throat", "throat pain", "congestion", "runny nose", "இருமல்", "खांसी"]) and not is_negated(["cough", "cold", "sore throat"]):
            extracted.main_complaint = "cough"
            extracted.symptoms.append("cough")
        elif any(w in text_lower for w in ["back pain", "lower back", "spine", "कमर दर्द", "முதுகு வலி"]) and not is_negated(["back pain"]):
            extracted.main_complaint = "back pain"
            extracted.symptoms.append("back pain")
            extracted.location = "back"
        elif any(w in text_lower for w in ["joint pain", "knee pain", "leg pain", "arm pain", "body pain", "body ache", "muscle pain", "விறைப்பு"]) and not is_negated(["joint pain", "knee pain", "body pain"]):
            extracted.main_complaint = "body and joint pain"
            extracted.symptoms.append("body and joint pain")
        elif any(w in text_lower for w in ["vomit", "nausea", "வாந்தி", "उल्टी"]) and not is_negated(["vomit", "nausea"]):
            extracted.main_complaint = "vomiting"
            extracted.symptoms.append("vomiting")
            extracted.location = "abdomen"
        elif any(w in text_lower for w in ["dizzy", "dizziness", "lightheaded", "faint", "vertigo", "மயக்கம்", "चक्कर"]) and not is_negated(["dizzy", "dizziness"]):
            extracted.main_complaint = "dizziness"
            extracted.symptoms.append("dizziness")
        elif any(w in text_lower for w in ["rash", "itching", "allergy", "burn", "wound", "cut", "injury"]) and not is_negated(["rash", "burn", "wound"]):
            extracted.main_complaint = "injury or skin reaction"
            extracted.symptoms.append("injury or skin reaction")
        else:
            # Check if text contains clinical words in English before defaulting
            # Exclude pure duration or scale statements from becoming a symptom
            is_duration_text = any(kw in text_lower for kw in ["minute", "min", "hour", "hr", "day", "week", "month", "yesterday", "morning", "ago"])
            is_scale_text = bool(re.search(r"^\s*(?:it is|level|scale|rate|rating|score|at)?\s*\b(10|[1-9])\b\s*$", text_lower))
            clean_words = re.sub(r"\b(i have|i feel|feeling|there is|a lot of|suffering from|patient reports|acute symptoms|acute discomfort|no other|no problem|let's finish|lets finish)\b", "", text_lower).strip()
            clean_words = re.sub(r"[^\w\s]", "", clean_words).strip()
            if not is_duration_text and not is_scale_text and clean_words and len(clean_words) > 2 and not any(kw in clean_words for kw in ["patient reports", "acute symptoms"]):
                extracted.main_complaint = clean_words
                extracted.symptoms.append(clean_words)
            else:
                extracted.main_complaint = "acute discomfort"
                extracted.symptoms.append("acute discomfort")

        # 2. Associated Symptoms
        if any(w in text_lower for w in ["shortness of breath", "breathing difficulty", "breath", "dyspnea", "மூச்சு"]) and extracted.main_complaint != "breathing difficulty" and not is_negated(["breath", "shortness of breath", "breathing difficulty"]):
            extracted.associated_symptoms.append("shortness of breath")
        if any(w in text_lower for w in ["sweat", "sweating", "diaphoresis", "வியர்வை", "पसीना"]) and not is_negated(["sweat"]):
            extracted.associated_symptoms.append("sweating")
        if any(w in text_lower for w in ["nausea", "vomit", "வாந்தி", "उल्टी"]) and extracted.main_complaint != "vomiting" and not is_negated(["nausea", "vomit"]):
            extracted.associated_symptoms.append("nausea")
        if any(w in text_lower for w in ["dizzy", "dizziness", "lightheaded", "faint", "மயக்கம்", "चक्कर"]) and extracted.main_complaint != "dizziness" and not is_negated(["dizzy"]):
            extracted.associated_symptoms.append("dizziness")
        if any(w in text_lower for w in ["palpitation", "racing heart", "rapid heartbeat"]):
            extracted.associated_symptoms.append("palpitations")

        # 3. Onset
        if any(w in text_lower for w in ["sudden", "abrupt", "suddenly", "all of a sudden", "acute", "திடீரென்று", "அचानक"]):
            extracted.onset = "sudden"
        elif any(w in text_lower for w in ["gradual", "slowly", "over time", "மெதுவாக", "धीरे"]):
            extracted.onset = "gradual"

        # 4. Duration Extraction (Parse numbers and units cleanly)
        # Look for e.g. "5 minutes", "20 mins", "2 hours", "3 days", "2 weeks", "1 month"
        duration_match = re.search(r"(\b\d+\b)\s*(?:to\s*\d+\s*)?(minute|minutes|min|mins|hour|hours|hr|hrs|day|days|week|weeks|wk|wks|month|months|mo|mos|year|years|yr|yrs|sec|seconds)\b", text_lower)
        if duration_match:
            val, unit = duration_match.group(1), duration_match.group(2)
            if "min" in unit:
                extracted.duration = f"{val} minutes"
            elif "hr" in unit or "hour" in unit:
                extracted.duration = f"{val} hours" if val != "1" else "1 hour"
            elif "day" in unit:
                extracted.duration = f"{val} days" if val != "1" else "1 day"
            elif "week" in unit or "wk" in unit:
                extracted.duration = f"{val} weeks" if val != "1" else "1 week"
            elif "month" in unit or "mo" in unit:
                extracted.duration = f"{val} months" if val != "1" else "1 month"
            elif "year" in unit or "yr" in unit:
                extracted.duration = f"{val} years" if val != "1" else "1 year"
            elif "sec" in unit:
                extracted.duration = f"{val} seconds"
        elif "half an hour" in text_lower or "half hour" in text_lower:
            extracted.duration = "30 minutes"
        elif "yesterday" in text_lower:
            extracted.duration = "since yesterday"
        elif "morning" in text_lower:
            extracted.duration = "since morning"
        elif "just now" in text_lower or "recently" in text_lower:
            extracted.duration = "just now"
        else:
            word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|forty|fifty)\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months)\b", text_lower)
            if word_match:
                extracted.duration = f"{word_match.group(1)} {word_match.group(2)}"

        # 5. Severity Extraction
        # Look for "8/10", "scale 8", "8 out of 10", standalone "8", "severe", "moderate", "mild"
        scale_match = re.search(r"\b(10|[1-9])\s*(?:out of|\/)\s*10\b", text_lower)
        if scale_match:
            extracted.severity = f"{scale_match.group(1)}/10"
        elif any(w in text_lower for w in ["severe", "unbearable", "extreme", "very high", "கடுமையான", "तेज", "തീവ്ര", "ತೀವ್ರ"]):
            extracted.severity = "severe"
        elif any(w in text_lower for w in ["moderate", "medium", "மிதமான", "मध्यम"]):
            extracted.severity = "moderate"
        elif any(w in text_lower for w in ["mild", "slight", "minor", "லேசான", "हल्का"]):
            extracted.severity = "mild"
        elif re.search(r"(?:scale|rate|rating|pain|level|grade|score)\s*(?:of\s*)?\b(10|[1-9])\b", text_lower):
            m = re.search(r"(?:scale|rate|rating|pain|level|grade|score)\s*(?:of\s*)?\b(10|[1-9])\b", text_lower)
            extracted.severity = f"{m.group(1)}/10"
        elif re.search(r"^\s*\b(10|[1-9])\b\s*(?:pain|level|severity|scale|grade|rate|rating)?\s*$", text_lower) and not any(tu in text_lower for tu in ["hour", "min", "day", "week", "sec", "மணி", "நேரம்", "घंटे"]):
            m = re.search(r"\b(10|[1-9])\b", text_lower)
            extracted.severity = f"{m.group(1)}/10"
        else:
            word_sev = {
                "one": "1/10", "two": "2/10", "three": "3/10", "four": "4/10", "five": "5/10",
                "six": "6/10", "seven": "7/10", "eight": "8/10", "nine": "9/10", "ten": "10/10"
            }
            for wnum, sval in word_sev.items():
                if re.search(rf"\b{wnum}\b", text_lower) and any(kw in text_lower for kw in ["scale", "rating", "pain", "level", "severity", "out of", "rate"]):
                    extracted.severity = sval
                    break

        # 6. Location
        if "chest" in text_lower or extracted.main_complaint == "chest discomfort":
            extracted.location = "chest"
        elif "abdomen" in text_lower or "stomach" in text_lower or extracted.main_complaint == "abdominal pain":
            extracted.location = "abdomen"
        elif "head" in text_lower or extracted.main_complaint == "headache":
            extracted.location = "head"
        elif "back" in text_lower or extracted.main_complaint == "back pain":
            extracted.location = "back"

        # 7. Missing Information List
        missing = []
        if not extracted.duration:
            missing.append("duration")
        if not extracted.severity:
            missing.append("severity")
        if extracted.main_complaint == "chest discomfort" and "shortness of breath" not in extracted.associated_symptoms:
            missing.append("breathing_difficulty")

        extracted.missing_information = missing
        return extracted

ai_service = AIService()
