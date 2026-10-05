import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.schemas.triage import TriageState
from app.services.ai_service import ai_service
from app.services.translation_service import translation_service
from app.services.red_flag_service import red_flag_service
from app.services.summary_service import summary_service
from app.services.adaptive_question_engine import adaptive_question_engine
from app.database.connection import sessions_cache

logger = logging.getLogger("medivoice.triage")

class TriageService:
    def get_or_create_session(
        self,
        session_id: str,
        language: str = "ta",
        patient_name: str = "Anonymous Patient",
        facility: str = "Emergency Triage Unit"
    ) -> Dict[str, Any]:
        if session_id not in sessions_cache:
            p_name = patient_name.strip() if patient_name and patient_name.strip() else "Anonymous Patient"
            fac = facility.strip() if facility and facility.strip() else "Emergency Triage Unit"
            state = TriageState(
                session_id=session_id,
                language=language,
                patient_name=p_name,
                facility=fac,
                priority="unknown"
            )
            sessions_cache[session_id] = {
                "session_id": session_id,
                "language": language,
                "patient_name": p_name,
                "facility": fac,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "triage_state": state.dict(),
                "messages": []
            }
        return sessions_cache[session_id]

    async def process_patient_response(
        self,
        session_id: str,
        patient_text: str,
        language: str
    ) -> Dict[str, Any]:
        session = self.get_or_create_session(session_id, language)
        state_dict = session["triage_state"]
        triage_state = TriageState(**state_dict)
        triage_state.language = language

        # 1. Store original patient message
        msg_id = len(session["messages"]) + 1
        original_msg = {
            "id": msg_id,
            "speaker": "patient",
            "original_text": patient_text,
            "translated_text": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        session["messages"].append(original_msg)

        # 2. Translate to English for processing
        english_text = await translation_service.translate_to_english(patient_text, language)
        original_msg["translated_text"] = english_text

        # 3. AI structured extraction
        extracted = await ai_service.extract_triage_info(english_text, language)

        # Check what question was last asked to map context accurately
        last_asked = triage_state.asked_questions[-1] if triage_state.asked_questions else None
        # We also track whether the last question sent was the completion_check via session flag
        last_question_type = session.get("last_question_type")
        
        # Check for completion response when asked "any other problem or complete?"
        patient_text_lower = patient_text.lower().strip()
        english_text_lower = english_text.lower().strip()
        
        NO_MORE_KEYWORDS = [
            "no", "none", "nothing", "complete", "finish", "done", "okay", "fine", "no other",
            "that's all", "thats all", "all good", "no problem", "no more", "we can complete",
            "இல்லை", "வேறு இல்லை", "வேறு எந்த", "முடித்துக் கொள்ளலாம்", "முடித்து விடுங்கள்",
            "போதும்", "இவ்ளோதான்", "வேறொன்றுமில்லை", "இல்லைங்க",
            "नहीं", "कोई अन्य समस्या नहीं", "और कुछ नहीं", "पूरा कर सकते हैं", "बस इतना ही", "ठीक है",
            "లేదు", "ఇంకేమీ లేదు", "ఇంతే", "పూర్తి చేయండి", "ఇల్ల", "ಬೇರೆ ಏನೂ ಇಲ್ಲ"
        ]
        
        is_completion_intent = any(kw in patient_text_lower or kw in english_text_lower for kw in NO_MORE_KEYWORDS)

        # Determine if extracted symptoms are truly new/meaningful (not just the fallback)
        GENERIC_FALLBACK_SYMPTOMS = {"acute discomfort"}
        has_real_new_symptoms = bool(
            [s for s in extracted.symptoms if s.lower() not in GENERIC_FALLBACK_SYMPTOMS]
        )

        # Mark complete if:
        # 1. Completion check was just asked and patient confirmed with a no-more-problems signal
        # 2. Patient explicitly says no more problems with no new specific symptoms
        if last_question_type == "completion_check" and is_completion_intent and not has_real_new_symptoms:
            triage_state.is_completed = True
            session["status"] = "completed"
        elif is_completion_intent and not has_real_new_symptoms and not extracted.duration:
            # Patient explicitly said complete or no more problems (even without explicit question)
            triage_state.is_completed = True
            session["status"] = "completed"

        # Update structured state
        if extracted.main_complaint and not triage_state.main_complaint:
            triage_state.main_complaint = extracted.main_complaint

        for sym in extracted.symptoms:
            if sym not in triage_state.symptoms:
                triage_state.symptoms.append(sym)

        for assoc in extracted.associated_symptoms:
            if assoc not in triage_state.associated_symptoms:
                triage_state.associated_symptoms.append(assoc)

        if extracted.onset:
            triage_state.onset = extracted.onset
            
        if extracted.duration:
            triage_state.duration = extracted.duration
        elif last_asked == "duration" and not triage_state.duration and len(english_text.strip()) > 0:
            # Fallback duration response from context
            triage_state.duration = english_text.strip()
            
        if extracted.severity:
            triage_state.severity = extracted.severity
        elif last_asked == "severity" and not triage_state.severity and len(english_text.strip()) > 0:
            # Fallback severity response from context
            triage_state.severity = english_text.strip()
            
        if extracted.location:
            triage_state.location = extracted.location

        for unc in extracted.uncertainties:
            if unc not in triage_state.uncertainties:
                triage_state.uncertainties.append(unc)

        for cnt in extracted.contradictions:
            if cnt not in triage_state.contradictions:
                triage_state.contradictions.append(cnt)

        # 4. Controlled Red-Flag Screening
        red_flags = red_flag_service.evaluate(triage_state)
        triage_state.red_flags = [rf.dict() for rf in red_flags]
        
        if red_flags:
            triage_state.priority = "high"
        elif triage_state.symptoms:
            triage_state.priority = "medium"

        # 5. Re-evaluate missing information
        missing = []
        if not triage_state.duration:
            missing.append("duration")
        if not triage_state.severity:
            missing.append("severity")
        if any(s in ["chest pain", "chest discomfort"] for s in triage_state.symptoms) and not any(b in triage_state.associated_symptoms for b in ["breathing difficulty", "shortness of breath"]):
            missing.append("breathing_difficulty")

        triage_state.missing_information = missing

        # 6. Generate Adaptive Follow-Up Question (guaranteed non-repeating)
        q_en, q_patient, missing_type = None, None, None
        if not triage_state.is_completed:
            q_en, q_patient, missing_type = await adaptive_question_engine.generate_next_question(triage_state)
            # Track asked clinical questions to prevent repeating them.
            # Do NOT track completion_check — it should be re-asked every turn
            # until patient explicitly confirms session completion.
            if missing_type and missing_type != "completion_check":
                if missing_type not in triage_state.asked_questions:
                    triage_state.asked_questions.append(missing_type)
            # Store last question type at session level (used for completion detection)
            session["last_question_type"] = missing_type

        if q_patient and not triage_state.is_completed:
            bot_msg = {
                "id": len(session["messages"]) + 1,
                "speaker": "assistant",
                "original_text": q_patient,
                "translated_text": q_en,
                "timestamp": datetime.utcnow().isoformat()
            }
            session["messages"].append(bot_msg)

        # 7. Generate English Summary
        triage_state.summary = summary_service.generate_english_summary(triage_state)

        # Save back to cache
        session["triage_state"] = triage_state.dict()
        session["status"] = "completed" if triage_state.is_completed else "active"
        session["updated_at"] = datetime.utcnow().isoformat()

        return {
            "session_id": session_id,
            "triage_state": triage_state.dict(),
            "patient_message": original_msg,
            "followup_question_en": q_en,
            "followup_question_patient": q_patient,
            "red_flags": [rf.dict() for rf in red_flags],
            "messages": session["messages"],
            "is_completed": triage_state.is_completed
        }

triage_service = TriageService()
