from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TriageState(BaseModel):
    session_id: str
    language: str = "ta"
    patient_name: Optional[str] = None
    facility: Optional[str] = None
    main_complaint: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    associated_symptoms: List[str] = Field(default_factory=list)
    relevant_history: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    red_flags: List[Dict[str, Any]] = Field(default_factory=list)
    priority: str = "unknown"  # high, medium, low, unknown
    summary: Optional[str] = None
    missing_information: List[str] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    is_completed: bool = False
    seen_at: Optional[str] = None
    seen_by: Optional[str] = None

class RedFlagDetail(BaseModel):
    rule_id: str
    rule_name: str
    priority: str  # high, medium
    triggered_symptoms: List[str]
    reason: str
    timestamp: str
    reference: str = "Emergency Severity Index / Standard Triage Framework"

class SessionCreateRequest(BaseModel):
    language: str = "ta"
    patient_name: Optional[str] = "Anonymous Patient"
    facility: Optional[str] = "Emergency Triage Unit"

class SessionResponse(BaseModel):
    session_id: str
    language: str
    patient_name: Optional[str] = None
    facility: Optional[str] = None
    status: str
    created_at: str
    triage_state: TriageState

class MarkSeenRequest(BaseModel):
    nurse_username: Optional[str] = "nurse_admin"
