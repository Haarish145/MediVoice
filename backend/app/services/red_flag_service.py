from datetime import datetime
from typing import List, Dict, Any
from app.schemas.triage import RedFlagDetail, TriageState

# Controlled Red-Flag Rule Definitions
RED_FLAG_RULES = [
    {
        "rule_id": "HIGH_PRIORITY_BREATHING",
        "rule_name": "Airway / Respiratory Distress Warning",
        "priority": "high",
        "keywords": [
            "breathing difficulty", "shortness of breath", "unable to breathe",
            "gasping", "suffocation", "dyspnea", "wheezing", "chest tightness with dyspnea",
            "மூச்சு விட முடியல", "மூச்சுத்திணறல்", "सांस लेने में तकलीफ", "सांस की बीमारी"
        ],
        "reason": "Acute respiratory difficulty reported. Requires immediate airway and oxygenation evaluation.",
        "reference": "Emergency Severity Index (ESI) Level 1/2 Protocol - Respiratory Distress"
    },
    {
        "rule_id": "HIGH_PRIORITY_CHEST_PAIN",
        "rule_name": "Cardiovascular / Acute Chest Pain Warning",
        "priority": "high",
        "keywords": [
            "chest pain", "chest discomfort", "chest pressure", "cardiac tightness", "pain radiating to arm",
            "heart attack", "crushing pain", "மார்பில் வலி", "நெஞ்சு வலி", "सीने में दर्द"
        ],
        "reason": "Acute chest pain/pressure detected. Requires immediate cardiac protocol screening and ECG.",
        "reference": "Emergency Severity Index (ESI) Level 2 Protocol - Acute Coronary Syndrome Risk"
    },
    {
        "rule_id": "HIGH_PRIORITY_NEURO",
        "rule_name": "Neurological / Acute Stroke Warning",
        "priority": "high",
        "keywords": [
            "slurred speech", "facial drooping", "arm weakness", "sudden numbness",
            "stroke", "sudden confusion", "paralysis", "பக்கவாதம்", "பேச்சு தடுமாற்றம்", "लकवा"
        ],
        "reason": "Acute neurological deficit / FAST stroke signs detected. Immediate stroke triage required.",
        "reference": "FAST Protocol / ESI Level 2 Acute Stroke Screening"
    },
    {
        "rule_id": "HIGH_PRIORITY_BLEEDING",
        "rule_name": "Severe Bleeding / Major Trauma Warning",
        "priority": "high",
        "keywords": [
            "heavy bleeding", "uncontrolled bleeding", "severe hemorrhage", "coughing blood",
            "vomiting blood", "அதிக ரத்தப்போக்கு", "रक्तस्राव"
        ],
        "reason": "Severe acute hemorrhage detected. Immediate vital signs evaluation and hemostasis required.",
        "reference": "Emergency Trauma Triage Guidelines"
    },
    {
        "rule_id": "HIGH_PRIORITY_CRITICAL_PAIN_GI",
        "rule_name": "Critical Pain / Acute Gastrointestinal Warning",
        "priority": "high",
        "keywords": [
            "10/10", "severe diarrhea", "acute diarrhea", "severe abdominal pain",
            "unbearable", "extreme pain", "தீவிரமான வயிற்றுப்போக்கு", "பேதி"
        ],
        "reason": "Maximal pain severity (10/10) or severe acute gastrointestinal distress reported. Immediate clinical evaluation for acute abdomen / dehydration required.",
        "reference": "Emergency Severity Index (ESI) Level 2 Protocol - Severe Pain / Hypovolemia Risk"
    },
    {
        "rule_id": "HIGH_PRIORITY_ACUTE_BURN_TRAUMA",
        "rule_name": "Acute Burn / Physical Trauma Warning",
        "priority": "high",
        "keywords": [
            "burn injury", "severe burn injury", "burn", "scald", "deep wound",
            "severe wound", "தீக்காயம்", "தீ காயம்", "जलना", "जलन", "பொള്ളൽ", "కాలిన గాయం"
        ],
        "reason": "Acute burn injury or physical trauma reported. Requires prompt wound assessment, cooling, analgesia, and infection prevention.",
        "reference": "Emergency Severity Index (ESI) Level 2/3 Protocol - Acute Burns & Trauma"
    }
]

class RedFlagService:
    def evaluate(self, triage_state: TriageState) -> List[RedFlagDetail]:
        triggered_flags: List[RedFlagDetail] = []
        
        # Combine all extracted text fields to screen against rule keywords
        combined_text = " ".join([
            triage_state.main_complaint or "",
            " ".join(triage_state.symptoms),
            " ".join(triage_state.associated_symptoms),
            triage_state.severity or "",
        ]).lower()
        
        for rule in RED_FLAG_RULES:
            matching_symptoms = []
            for kw in rule["keywords"]:
                if kw in combined_text:
                    matching_symptoms.append(kw)
            
            if matching_symptoms:
                flag = RedFlagDetail(
                    rule_id=rule["rule_id"],
                    rule_name=rule["rule_name"],
                    priority=rule["priority"],
                    triggered_symptoms=matching_symptoms,
                    reason=rule["reason"],
                    timestamp=datetime.utcnow().isoformat(),
                    reference=rule["reference"]
                )
                triggered_flags.append(flag)
                
        return triggered_flags

red_flag_service = RedFlagService()
