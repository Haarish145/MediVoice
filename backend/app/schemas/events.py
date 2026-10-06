from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class WebSocketEvent(BaseModel):
    event: str = Field(..., description="Event name, e.g. symptom_detected, triage_state_updated")
    session_id: str = Field(..., description="Session ID formatted as MV-YYYY-NNNN")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO-8601 UTC timestamp")
