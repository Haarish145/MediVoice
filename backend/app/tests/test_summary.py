import pytest
import re
from app.services.triage_service import triage_service

@pytest.mark.asyncio
async def test_tamil_speech_to_english_summary():
    # Simulate Tamil patient voice input
    patient_tamil_text = "எனக்கு நெஞ்சு வலி 5 நிமிடங்களாக இருக்கிறது"
    session_id = "test-tamil-triage-1"
    
    result = await triage_service.process_patient_response(
        session_id=session_id,
        patient_text=patient_tamil_text,
        language="ta"
    )
    
    # 1. Original text preserves patient Tamil speech
    assert result["patient_message"]["original_text"] == patient_tamil_text
    
    # 2. Translated text is in English
    translated = result["patient_message"]["translated_text"]
    assert translated is not None
    assert "chest" in translated.lower() or "pain" in translated.lower()
    
    # 3. Triage State has clinical English fields
    state = result["triage_state"]
    assert state["main_complaint"] == "chest discomfort"
    assert state["duration"] == "5 minutes"
    assert state["location"] == "chest"
    assert state["priority"] == "high"
    
    # 4. English Triage Summary must NOT contain any non-ASCII characters
    summary = state["summary"]
    assert summary is not None
    non_ascii_chars = re.findall(r"[^\x00-\x7F]", summary)
    assert len(non_ascii_chars) == 0, f"Summary contains non-ASCII characters: {non_ascii_chars}"
    
    # 5. Summary matches required clinical phrasing
    assert "Patient reports chest discomfort." in summary
    assert "Symptoms started approximately 5 minutes ago." in summary
    assert "Patient describes discomfort in the chest." in summary
    assert "Severity assessment is currently being collected." in summary
