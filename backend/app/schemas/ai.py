from typing import List, Optional
from pydantic import BaseModel, Field

class AIStructuredExtraction(BaseModel):
    main_complaint: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    associated_symptoms: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None
    uncertainties: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
