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

        # 1. Main Complaint & Symptoms Extraction (Canonical English)
        if any(w in text_lower for w in ["chest pain", "chest discomfort", "angina", "tightness in chest", "pressure in chest", "மார்பில் வலி", "நெஞ்சு வலி", "சீனே"]):
            extracted.main_complaint = "chest discomfort"
            extracted.symptoms.append("chest discomfort")
            extracted.location = "chest"
        elif any(w in text_lower for w in ["breath", "breathing difficulty", "shortness of breath", "dyspnea", "suffocat", "gasp", "மூச்சு"]):
            extracted.main_complaint = "breathing difficulty"
            extracted.symptoms.append("breathing difficulty")
        elif any(w in text_lower for w in ["abdominal pain", "stomach pain", "stomach ache", "belly", "வயிறு வலி", "पेट दर्द"]):
            extracted.main_complaint = "abdominal pain"
            extracted.symptoms.append("abdominal pain")
            extracted.location = "abdomen"
        elif any(w in text_lower for w in ["headache", "head pain", "migraine", "தலைவலி", "सिरदर्द"]):
            extracted.main_complaint = "headache"
            extracted.symptoms.append("headache")
            extracted.location = "head"
        elif any(w in text_lower for w in ["stroke", "slurred speech", "facial drooping", "paralysis", "பக்கவாதம்", "लकवा"]):
            extracted.main_complaint = "stroke symptoms"
            extracted.symptoms.append("slurred speech")
        elif any(w in text_lower for w in ["bleed", "hemorrhage", "blood", "ரத்தப்போக்கு", "रक्तस्राव"]):
            extracted.main_complaint = "acute bleeding"
            extracted.symptoms.append("acute bleeding")
        elif any(w in text_lower for w in ["fever", "chills", "high temperature", "காய்ச்சல்", "बुखार"]):
            extracted.main_complaint = "fever"
            extracted.symptoms.append("fever")
        else:
            # Fallback: keep complaint concise and clinical
            extracted.main_complaint = "acute discomfort"
            extracted.symptoms.append("acute discomfort")

        # 2. Associated Symptoms
        if any(w in text_lower for w in ["shortness of breath", "breathing difficulty", "breath", "dyspnea", "மூச்சு"]) and extracted.main_complaint != "breathing difficulty":
            extracted.associated_symptoms.append("shortness of breath")
        if any(w in text_lower for w in ["sweat", "sweating", "diaphoresis", "வியர்வை", "पसीना"]):
            extracted.associated_symptoms.append("sweating")
        if any(w in text_lower for w in ["nausea", "vomit", "வாந்தி", "उल्टी"]):
            extracted.associated_symptoms.append("nausea")
        if any(w in text_lower for w in ["dizzy", "dizziness", "lightheaded", "faint", "மயக்கம்", "चक्कर"]):
            extracted.associated_symptoms.append("dizziness")
        if any(w in text_lower for w in ["palpitation", "racing heart", "rapid heartbeat"]):
            extracted.associated_symptoms.append("palpitations")

        # 3. Onset
        if any(w in text_lower for w in ["sudden", "abrupt", "suddenly", "all of a sudden", "acute", "திடீரென்று", "अचानक"]):
            extracted.onset = "sudden"
        elif any(w in text_lower for w in ["gradual", "slowly", "over time", "மெதுவாக", "धीरे"]):
            extracted.onset = "gradual"

        # 4. Duration Extraction (Parse numbers and units cleanly)
        # Look for e.g. "5 minutes", "20 mins", "2 hours", "3 days"
        duration_match = re.search(r"(\b\d+\b)\s*(?:to\s*\d+\s*)?(minute|minutes|min|mins|hour|hours|hr|hrs|day|days|sec|seconds)", text_lower)
        if duration_match:
            val, unit = duration_match.group(1), duration_match.group(2)
            if "min" in unit:
                extracted.duration = f"{val} minutes"
            elif "hr" in unit or "hour" in unit:
                extracted.duration = f"{val} hours" if val != "1" else "1 hour"
            elif "day" in unit:
                extracted.duration = f"{val} days" if val != "1" else "1 day"
            elif "sec" in unit:
                extracted.duration = f"{val} seconds"
        else:
            # Word numbers: five minutes, twenty minutes, etc.
            word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|forty|fifty)\s+(minute|minutes|hour|hours|day|days)\b", text_lower)
            if word_match:
                extracted.duration = f"{word_match.group(1)} {word_match.group(2)}"

        # 5. Severity Extraction
        # Look for "8/10", "scale 8", "severe", "moderate", "mild"
        scale_match = re.search(r"\b([1-9]|10)\s*(?:out of|\/)\s*10\b", text_lower)
        if scale_match:
            extracted.severity = f"{scale_match.group(1)}/10"
        elif any(w in text_lower for w in ["severe", "unbearable", "extreme", "very high", "கடுமையான", "तेज"]):
            extracted.severity = "severe"
        elif any(w in text_lower for w in ["moderate", "medium", "மிதமான"]):
            extracted.severity = "moderate"
        elif any(w in text_lower for w in ["mild", "slight", "minor", "லேசான"]):
            extracted.severity = "mild"
        elif re.search(r"\b([1-9]|10)\b", text_lower) and "scale" in text_lower:
            m = re.search(r"\b([1-9]|10)\b", text_lower)
            extracted.severity = f"{m.group(1)}/10"

        # 6. Location
        if "chest" in text_lower or extracted.main_complaint == "chest discomfort":
            extracted.location = "chest"
        elif "abdomen" in text_lower or "stomach" in text_lower or extracted.main_complaint == "abdominal pain":
            extracted.location = "abdomen"
        elif "head" in text_lower or extracted.main_complaint == "headache":
            extracted.location = "head"

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
