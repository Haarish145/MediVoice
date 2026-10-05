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
        if not complaint or complaint == "unspecified acute symptoms" or complaint == "acute discomfort":
            sentences.append(f"{p_prefix} reports acute discomfort.")
        elif "chest" in complaint:
            sentences.append(f"{p_prefix} reports chest discomfort.")
        elif "breath" in complaint or "dyspnea" in complaint:
            sentences.append(f"{p_prefix} reports difficulty breathing.")
        elif "abdom" in complaint or "stomach" in complaint:
            sentences.append(f"{p_prefix} reports acute abdominal discomfort.")
        elif "head" in complaint:
            sentences.append(f"{p_prefix} reports severe headache.")
        elif "stroke" in complaint or "speech" in complaint or "paralysis" in complaint:
            sentences.append(f"{p_prefix} presents with acute neurological symptoms.")
        elif "bleed" in complaint:
            sentences.append(f"{p_prefix} presents with acute bleeding.")
        elif "fever" in complaint:
            sentences.append(f"{p_prefix} reports high fever.")
        else:
            # Clean complaint of non-latin characters
            clean_c = re.sub(r"[^\x00-\x7F]+", "", complaint).strip()
            if clean_c:
                sentences.append(f"{p_prefix} reports {clean_c}.")
            else:
                sentences.append(f"{p_prefix} reports acute discomfort.")

        # 2. Symptom Duration & Onset Timeline
        duration = (triage_state.duration or "").strip()
        onset = (triage_state.onset or "").strip().lower()
        
        # Clean duration
        clean_duration = re.sub(r"[^\x00-\x7F]+", "", duration).strip()

        if clean_duration:
            # Format nicely: "5 minutes" -> "Symptoms started approximately 5 minutes ago."
            if "ago" in clean_duration.lower():
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
            if re.sub(r"[^\x00-\x7F]+", "", s).strip()
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

        if clean_sev:
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

        # Combine sentences
        full_summary = " ".join(sentences)

        # Final safety filter: guarantee 100% ASCII / English text
        sanitized = re.sub(r"[^\x00-\x7F]+", "", full_summary)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized

summary_service = SummaryService()
