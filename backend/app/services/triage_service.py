import logging
import re
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

        # Validate patient input (ignore empty, whitespace, or micro-noise < 2 chars, but ALLOW digits like "8")
        clean_text = (patient_text or "").strip()
        if not clean_text or (len(clean_text) < 2 and not re.search(r"\d", clean_text)):
            logger.info(f"Ignoring empty or noise input: '{patient_text}'")
            active_q = session["messages"][-1]["original_text"] if session.get("messages") else "Please describe your symptoms"
            active_q_en = session["messages"][-1].get("translated_text") if session.get("messages") else "Please describe your symptoms"
            return {
                "session_id": session_id,
                "triage_state": triage_state.dict(),
                "followup_question_en": active_q_en,
                "followup_question_patient": active_q,
                "patient_message": None,
                "messages": session["messages"],
                "is_completed": triage_state.is_completed,
                "red_flags": triage_state.red_flags
            }

        # Check for microphone echo of the bot's own question
        last_bot_msg = None
        for m in reversed(session.get("messages", [])):
            if m.get("speaker") == "assistant":
                last_bot_msg = m
                break

        if last_bot_msg:
            last_bot_orig = (last_bot_msg.get("original_text") or "").strip().lower()
            last_bot_trans = (last_bot_msg.get("translated_text") or "").strip().lower()
            p_lower = clean_text.lower()
            if (
                p_lower == last_bot_orig
                or p_lower == last_bot_trans
                or (len(p_lower) > 8 and (p_lower in last_bot_orig or p_lower in last_bot_trans))
                or (len(last_bot_orig) > 8 and last_bot_orig in p_lower)
            ):
                logger.warning(f"Ignored microphone echo of bot question: '{clean_text}'")
                return {
                    "session_id": session_id,
                    "triage_state": triage_state.dict(),
                    "followup_question_en": last_bot_msg.get("translated_text"),
                    "followup_question_patient": last_bot_msg.get("original_text"),
                    "patient_message": None,
                    "messages": session["messages"],
                    "is_completed": triage_state.is_completed,
                    "red_flags": triage_state.red_flags
                }

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
        last_question_type = session.get("last_question_type")
        
        # Check for completion response when asked "any other problem or complete?"
        patient_text_lower = patient_text.lower().strip()
        english_text_lower = english_text.lower().strip()

        NO_MORE_KEYWORDS = [
            "no", "none", "nothing", "complete", "finish", "done", "no other",
            "that's all", "thats all", "all good", "no problem", "no more", "we can complete",
            "let's finish", "lets finish", "let us finish", "we can finish", "let us complete",
            "no other problem", "no problems", "nothing else", "no further",
            "இல்லை", "வேறு இல்லை", "வேறு எந்த", "முடித்துக் கொள்ளலாம்", "முடித்து விடுங்கள்",
            "போதும்", "இவ்ளோதான்", "வேறொன்றுமில்லை", "இல்லைங்க",
            "नहीं", "कोई अन्य समस्या नहीं", "और कुछ नहीं", "पूरा कर सकते हैं", "बस इतना ही",
            "లేదు", "ఇంకేమీ లేదు", "ఇంతే", "పూర్తి చేయండి",
            "ಇಲ್ಲ", "ಬೇರೆ ಏನೂ ಇಲ್ಲ", "ಮುಗಿಸಬಹುದು",
            "അല്ല", "മറ്റ് പ്രശ്നങ്ങളില്ല", "പൂർത്തിയാക്കാം",
            "না", "আর কিছু নেই", "সম্পন্ন করুন",
            "नाही", "काही नाही", "पूर्ण करू शकता",
            "ના", "બીજું કંઈ નથી", "પૂર્ણ કરી શકીએ"
        ]

        YES_KEYWORDS = [
            "yes", "yeah", "yep", "i have", "yes i have", "yes i do", "there is", "have other",
            "more symptom", "another problem", "also have", "i also", "still have", "and i have",
            "ஆம்", "ஆமாம்", "இருக்கிறது", "இருக்கு", "ஆமா", "வேற பிரச்சனை இருக்கு", "வேறு உள்ளது",
            "हाँ", "हां", "हा", "हाँ है", "है", "मुझे और तकलीफ है", "अन्य समस्या है", "और समस्या", "हाँ मुझे",
            "అవును", "ఉంది", "ఉన్నాయి", "నాకు ఇంకా సమస్య ఉంది",
            "ಹೌದು", "ಇದೆ", "ನನಗೆ ಇನ್ನೊಂದು ಸಮಸ್ಯೆ ಇದೆ",
            "അതെ", "ഉണ്ട്", "എനിക്ക് മറ്റ് പ്രശ്നങ്ങൾ ഉണ്ട്",
            "হ্যাঁ", "হ্যা", "আছে", "আমার আরও সমস্যা আছে",
            "होय", "हो", "आहे", "मला आणखी त्रास आहे",
            "હા", "છે", "મને બીજી તકલીફ છે",
            "ਹਾਂ", "ਹੈ", "ਮੈਨੂੰ ਹੋਰ ਸਮੱਸਿਆ ਹੈ",
            "ହଁ", "ଅଛି", "ମୋର ଆଉ ସମସ୍ୟା ଅଛି",
            "হয়", "আছে", "মোৰ আৰু সমস্যা আছে"
        ]

        EXPLICIT_COMPLETE_KEYWORDS = [
            "complete", "finish", "done", "that's all", "thats all", "all good", "no more", "we can complete",
            "let's finish", "lets finish", "let us finish", "we can finish", "let us complete",
            "முடித்துக் கொள்ளலாம்", "முடித்து விடுங்கள்", "போதும்", "இவ்ளோதான்", "வேறொன்றுமில்லை",
            "पूरा कर सकते हैं", "बस इतना ही", "పూర్తి చేయండి", "ముగಿಸಬಹುದು", "പൂർത്തിയാക്കാം",
            "সম্পন্ন করুন", "पूर्ण करू शकता", "પૂર્ણ કરી શકીએ"
        ]

        is_no_intent = any(kw in patient_text_lower or kw in english_text_lower for kw in NO_MORE_KEYWORDS)
        is_yes_intent = any(kw in patient_text_lower or kw in english_text_lower for kw in YES_KEYWORDS)
        is_explicit_complete = any(kw in patient_text_lower or kw in english_text_lower for kw in EXPLICIT_COMPLETE_KEYWORDS)

        # Determine if extracted symptoms are truly new/meaningful (not just the fallback or previously logged)
        GENERIC_FALLBACK_SYMPTOMS = {"acute discomfort", "unspecified acute symptoms", "patient reports acute symptoms"}
        has_real_new_symptoms = bool(
            [s for s in extracted.symptoms if s.lower() not in GENERIC_FALLBACK_SYMPTOMS and s not in triage_state.symptoms and not any(kw in s.lower() for kw in NO_MORE_KEYWORDS)]
        ) or bool(
            [s for s in extracted.associated_symptoms if s not in triage_state.associated_symptoms and not any(kw in s.lower() for kw in NO_MORE_KEYWORDS)]
        )

        force_question = None

        # ── Additional-symptom loop state (stored at session level) ──────────
        # session["in_additional_flow"]   : bool  – are we inside an extra-round?
        # session["add_flow_step"]         : str   – "description" | "duration" | "severity"
        # session["current_additional"]   : dict  – partial round being built
        # ────────────────────────────────────────────────────────────────────

        if last_question_type == "completion_check":
            if is_no_intent and not has_real_new_symptoms and not is_yes_intent:
                # Patient said "no more" → complete intake
                triage_state.is_completed = True
                session["status"] = "completed"
                session["in_additional_flow"] = False
                session["add_flow_step"] = None
                session["current_additional"] = {}

            elif has_real_new_symptoms or is_yes_intent:
                # Patient said "yes" (possibly describing the new symptom inline)
                session["in_additional_flow"] = True
                if has_real_new_symptoms:
                    # They already told us the symptom in the same sentence
                    desc = english_text.strip() or patient_text.strip()
                    if any(err in desc.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                        desc = patient_text.strip()
                    session["current_additional"] = {"description": desc, "duration": "", "severity": ""}
                    session["add_flow_step"] = "duration"
                    force_question = "additional_duration"
                else:
                    # Pure "yes" → ask them to describe
                    session["current_additional"] = {}
                    session["add_flow_step"] = "description"
                    force_question = "additional_symptoms_prompt"
            else:
                # Unclear → treat as "no more problems" to prevent loop
                triage_state.is_completed = True
                session["status"] = "completed"
                session["in_additional_flow"] = False
                session["add_flow_step"] = None
                session["current_additional"] = {}

        elif last_question_type == "additional_symptoms_prompt":
            # Patient just described their additional symptom
            if is_no_intent and not has_real_new_symptoms:
                triage_state.is_completed = True
                session["status"] = "completed"
                session["in_additional_flow"] = False
                session["add_flow_step"] = None
                session["current_additional"] = {}
            else:
                desc = english_text.strip() or patient_text.strip()
                if any(err in desc.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                    desc = patient_text.strip()
                session["current_additional"] = {"description": desc, "duration": "", "severity": ""}
                session["add_flow_step"] = "duration"
                session["in_additional_flow"] = True
                force_question = "additional_duration"

        elif last_question_type == "additional_duration":
            # Patient answered "how long" for the additional symptom
            dur = english_text.strip() or patient_text.strip()
            if any(err in dur.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                dur = patient_text.strip()
            ca = session.get("current_additional") or {}
            ca["duration"] = dur
            session["current_additional"] = ca
            session["add_flow_step"] = "severity"
            session["in_additional_flow"] = True
            force_question = "additional_severity"

        elif last_question_type == "additional_severity":
            # Patient answered severity for the additional symptom → flush round
            sev = english_text.strip() or patient_text.strip()
            if any(err in sev.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                sev = patient_text.strip()
            ca = session.get("current_additional") or {}
            ca["severity"] = sev
            session["current_additional"] = ca
            # Store completed round in triage state
            triage_state.additional_complaints.append({
                "description": ca.get("description", ""),
                "duration": ca.get("duration", ""),
                "severity": ca.get("severity", "")
            })
            session["current_additional"] = {}
            session["add_flow_step"] = None
            session["in_additional_flow"] = False
            # Now ask completion_check again
            force_question = "completion_check"

        elif last_question_type == "duration" and session.get("in_additional_flow"):
            # Legacy path – kept for backward compat; ask severity next
            session["add_flow_step"] = "severity"
            force_question = "additional_severity"

        elif is_explicit_complete and not has_real_new_symptoms and not extracted.duration and triage_state.symptoms:
            # Patient explicitly said complete / no more problems outside of the loop
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
            
        time_cues = ["min", "hour", "day", "week", "sec", "yesterday", "morning", "night", "since", "for", "ago",
                     "மணி", "நேரம்", "நாள்", "வாரம்", "நேற்று", "घंटे", "दिन", "सुबह", "రోజు", "గంట"]
        has_time_cue = any(tk in english_text_lower or tk in patient_text_lower for tk in time_cues) or bool(re.search(r"\d+", english_text))

        is_in_add_round = session.get("in_additional_flow") or last_question_type in ["additional_duration", "additional_severity", "additional_symptoms_prompt"]
        if not is_in_add_round:
            if extracted.duration:
                triage_state.duration = extracted.duration
            elif last_asked == "duration" and not triage_state.duration:
                # Always capture the raw answer when duration was the last question asked,
                # but guard against generic fallback strings.
                cand = english_text.strip() if english_text.strip() else patient_text.strip()
                if not any(err in cand.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                    triage_state.duration = cand
                else:
                    triage_state.duration = patient_text.strip()
                
            sev_cues = ["severe", "mild", "moderate", "bad", "high", "low", "extreme", "pain", "scale",
                        "கடுமையான", "அதிகம்", "குறைவு", "तेज", "ज्यादा", "कम", "తీవ్ర", "ತೀವ್ರ"]
            has_sev_cue = any(sk in english_text_lower or sk in patient_text_lower for sk in sev_cues) or bool(re.search(r"\b([1-9]|10)\b", english_text))

            if extracted.severity:
                triage_state.severity = extracted.severity
            elif last_asked == "severity" and not triage_state.severity:
                # Always capture the raw answer when severity was the last question asked,
                # but guard against generic fallback strings and format numbers cleanly.
                cand = english_text.strip() if english_text.strip() else patient_text.strip()
                if not any(err in cand.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                    m = re.search(r"\b(10|[1-9])\b", cand)
                    triage_state.severity = f"{m.group(1)}/10" if m else cand
                else:
                    m = re.search(r"\b(10|[1-9])\b", patient_text)
                    triage_state.severity = f"{m.group(1)}/10" if m else patient_text.strip()
                
            if extracted.location and not triage_state.location:
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
        # IMPORTANT: Exclude question types already asked so they NEVER repeat,
        # regardless of whether the AI successfully parsed the patient's answer.
        missing = []
        if not triage_state.duration and "duration" not in triage_state.asked_questions:
            missing.append("duration")
        if not triage_state.severity and "severity" not in triage_state.asked_questions:
            missing.append("severity")
        if (any(s in ["chest pain", "chest discomfort"] for s in triage_state.symptoms)
                and not any(b in triage_state.associated_symptoms for b in ["breathing difficulty", "shortness of breath"])
                and "breathing_difficulty" not in triage_state.asked_questions):
            missing.append("breathing_difficulty")

        triage_state.missing_information = missing

        # 6. Generate Adaptive Follow-Up Question (guaranteed non-repeating)
        q_en, q_patient, missing_type = None, None, None
        if not triage_state.is_completed:
            q_en, q_patient, missing_type = await adaptive_question_engine.generate_next_question(
                triage_state=triage_state,
                force_question_type=force_question
            )
            # Track asked clinical questions to prevent repeating them.
            # Also track breathing_difficulty. Do NOT track completion_check or additional_symptoms_prompt.
            if missing_type and missing_type not in ["completion_check", "additional_symptoms_prompt"]:
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
