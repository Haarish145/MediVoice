import re
from typing import Dict, Any, List
from app.schemas.triage import TriageState

class SummaryService:
    """
    Generates structured, professional English Clinical Triage Summaries.
    Guarantees 100% natural clinical English phrasing without raw regional language tokens.
    """
    def generate_english_summary(self, triage_state: TriageState) -> str:
        sentences: List[str] = []

        # 1. Primary Clinical Presentation
        p_name = (triage_state.patient_name or "").strip()
        p_prefix = f"Patient {p_name}" if p_name and p_name.lower() != "anonymous patient" else "Patient"
        complaint = (triage_state.main_complaint or "").strip().lower()

        # If complaint contains non-ASCII characters, translate through Indic symptom parser
        if any(ord(c) >= 128 for c in complaint):
            from app.services.translation_service import parse_indic_symptom
            mapped_sym = parse_indic_symptom(complaint)
            if mapped_sym:
                complaint = mapped_sym.lower()

        if not complaint or complaint in ["unspecified acute symptoms", "acute discomfort", "patient reports acute symptoms"]:
            sentences.append(f"{p_prefix} reports acute discomfort.")
        elif "diarrhea" in complaint or "diarrhoea" in complaint or "loose motion" in complaint:
            sentences.append(f"{p_prefix} reports severe acute diarrhea." if "severe" in complaint else f"{p_prefix} reports acute diarrhea.")
        elif "burn" in complaint or "scald" in complaint:
            sentences.append(f"{p_prefix} presents with an acute severe burn injury." if "severe" in complaint else f"{p_prefix} presents with an acute burn injury.")
        elif "wound" in complaint or "injury" in complaint:
            sentences.append(f"{p_prefix} presents with an acute physical wound and injury.")
        elif "chest" in complaint:
            sentences.append(f"{p_prefix} reports chest discomfort.")
        elif "breath" in complaint or "dyspnea" in complaint:
            sentences.append(f"{p_prefix} reports difficulty breathing.")
        elif "abdom" in complaint or "stomach" in complaint:
            sentences.append(f"{p_prefix} reports acute abdominal pain and discomfort.")
        elif "head" in complaint:
            sentences.append(f"{p_prefix} reports severe headache.")
        elif "stroke" in complaint or "speech" in complaint or "paralysis" in complaint:
            sentences.append(f"{p_prefix} presents with acute neurological symptoms.")
        elif "bleed" in complaint:
            sentences.append(f"{p_prefix} presents with acute bleeding.")
        elif "fever" in complaint:
            sentences.append(f"{p_prefix} reports high fever.")
        elif "cough" in complaint or "cold" in complaint:
            sentences.append(f"{p_prefix} reports persistent cough.")
        elif "back" in complaint:
            sentences.append(f"{p_prefix} reports back pain.")
        elif "joint" in complaint or "body" in complaint or "knee" in complaint or "leg" in complaint:
            sentences.append(f"{p_prefix} reports body and joint pain.")
        elif "vomit" in complaint or "nausea" in complaint:
            sentences.append(f"{p_prefix} reports nausea and vomiting.")
        elif "dizzy" in complaint:
            sentences.append(f"{p_prefix} reports dizziness.")
        else:
            # Clean complaint of non-latin characters and generic error phrases
            clean_c = re.sub(r"[^\x00-\x7F]+", "", complaint).strip()
            if any(err in clean_c for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                sentences.append(f"{p_prefix} reports acute discomfort.")
            elif clean_c:
                sentences.append(f"{p_prefix} reports {clean_c}.")
            else:
                sentences.append(f"{p_prefix} reports acute discomfort.")

        # 2. Symptom Duration & Onset Timeline
        duration = (triage_state.duration or "").strip()
        onset = (triage_state.onset or "").strip().lower()
        
        # If duration contains non-ASCII characters, translate through Indic duration parser
        if any(ord(c) >= 128 for c in duration):
            from app.services.translation_service import parse_indic_duration
            mapped_dur = parse_indic_duration(duration)
            if mapped_dur:
                duration = mapped_dur
        
        # Clean duration of non-latin characters and invalid fallback phrases
        clean_duration = re.sub(r"[^\x00-\x7F]+", "", duration).strip()
        if any(err in clean_duration.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
            clean_duration = ""

        if clean_duration:
            # Format nicely
            if clean_duration.lower().startswith("since ") or clean_duration.lower().startswith("from "):
                sentences.append(f"Symptoms started {clean_duration.lower()}.")
            elif clean_duration.lower().startswith("about "):
                dur_val = clean_duration[6:].strip()
                sentences.append(f"Symptoms started approximately {dur_val} ago.")
            elif "ago" in clean_duration.lower():
                sentences.append(f"Symptoms started {clean_duration}.")
            elif "for " in clean_duration.lower():
                dur_val = clean_duration.lower().replace("for ", "").strip()
                sentences.append(f"Symptoms started approximately {dur_val} ago.")
            else:
                sentences.append(f"Symptoms started approximately {clean_duration} ago.")
        elif onset:
            sentences.append(f"Symptoms began with {onset} onset.")
        else:
            sentences.append("Symptom duration is currently under evaluation.")

        # 3. Description, Location & Associated Symptoms
        loc = (triage_state.location or "").strip().lower()
        clean_loc = re.sub(r"[^\x00-\x7F]+", "", loc).strip()
        
        # If complaint is chest discomfort, default location is chest if not otherwise set
        if not clean_loc and "chest" in complaint:
            clean_loc = "chest"

        assoc_symptoms = [
            re.sub(r"[^\x00-\x7F]+", "", s).strip()
            for s in triage_state.associated_symptoms
            if re.sub(r"[^\x00-\x7F]+", "", s).strip() and not any(err in s.lower() for err in ["patient reports", "acute symptoms"])
        ]

        if clean_loc and assoc_symptoms:
            sentences.append(f"Patient describes discomfort in the {clean_loc}, with associated {', '.join(assoc_symptoms)}.")
        elif clean_loc:
            sentences.append(f"Patient describes discomfort in the {clean_loc}.")
        elif assoc_symptoms:
            sentences.append(f"Associated symptoms reported: {', '.join(assoc_symptoms)}.")

        # 4. Current Clinical Assessment / Missing Information Status
        sev = (triage_state.severity or "").strip()
        clean_sev = re.sub(r"[^\x00-\x7F]+", "", sev).strip()
        if any(err in clean_sev.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
            clean_sev = ""

        if clean_sev:
            # Format bare digits 1-10 as /10
            if re.match(r"^\b(10|[1-9])\b$", clean_sev):
                clean_sev = f"{clean_sev}/10"
            sentences.append(f"Reported severity is rated as {clean_sev}.")
        elif "severity" in triage_state.missing_information or not triage_state.severity:
            sentences.append("Severity assessment is currently being collected.")
        elif "duration" in triage_state.missing_information and not clean_duration:
            sentences.append("Duration assessment is currently being collected.")
        else:
            sentences.append("Clinical assessment is actively in progress.")

        # 5. Red-Flag Emergency Protocols (if triggered)
        if triage_state.red_flags:
            flags = [f.get("rule_name", "Red Flag Alert") for f in triage_state.red_flags]
            sentences.append(f"HIGH PRIORITY RED FLAGS DETECTED: {', '.join(flags)}.")

        # 6. Additional Complaints (collected during post-intake loop)
        add_complaints = getattr(triage_state, "additional_complaints", [])
        if add_complaints:
            from app.services.translation_service import parse_indic_symptom, parse_indic_duration
            idx = 1
            for ac in add_complaints:
                raw_desc = (ac.get("description") or "").strip()
                if any(ord(c) >= 128 for c in raw_desc):
                    parsed_d = parse_indic_symptom(raw_desc)
                    if parsed_d:
                        raw_desc = parsed_d
                desc = re.sub(r"[^\x00-\x7F]+", "", raw_desc).strip()

                raw_dur = (ac.get("duration") or "").strip()
                if any(ord(c) >= 128 for c in raw_dur):
                    parsed_dur = parse_indic_duration(raw_dur)
                    if parsed_dur:
                        raw_dur = parsed_dur
                dur  = re.sub(r"[^\x00-\x7F]+", "", raw_dur).strip()

                raw_sev = (ac.get("severity") or "").strip()
                m_sev = re.search(r"\b(10|[1-9])\b", raw_sev)
                if m_sev:
                    raw_sev = f"{m_sev.group(1)}/10"
                sev  = re.sub(r"[^\x00-\x7F]+", "", raw_sev).strip()

                # Skip invalid generic strings
                if not desc or any(err in desc.lower() for err in ["patient reports", "acute symptoms", "acute discomfort"]):
                    continue
                parts = [f"Additional complaint {idx}: {desc}"]
                idx += 1
                if dur and not any(err in dur.lower() for err in ["patient reports", "acute symptoms"]):
                    parts.append(f"duration {dur}")
                if sev and not any(err in sev.lower() for err in ["patient reports", "acute symptoms"]):
                    parts.append(f"severity {sev}")
                sentences.append(". ".join(parts) + ".")

        # Combine sentences
        full_summary = " ".join(sentences)

        # Final safety filter: guarantee 100% ASCII / English text
        sanitized = re.sub(r"[^\x00-\x7F]+", "", full_summary)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized

summary_service = SummaryService()
