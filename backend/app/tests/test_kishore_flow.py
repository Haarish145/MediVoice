import pytest
from app.services.triage_service import triage_service

@pytest.mark.asyncio
async def test_complete_kishore_triage_flow():
    sid = "test-kishore-session-1"
    session = triage_service.get_or_create_session(sid, "ta", "kishore", "Apollo Emergency Triage")

    # Verify initial greeting / question is present in messages from start
    assert len(session["messages"]) == 1
    assert session["messages"][0]["speaker"] == "assistant"
    assert "உடல்நிலை" in session["messages"][0]["original_text"]

    # Step 1: Patient complains of severe diarrhea
    r1 = await triage_service.process_patient_response(sid, "தீவிரமான வயிற்றுப்போக்கு", "ta")
    assert r1["patient_message"]["original_text"] == "தீவிரமான வயிற்றுப்போக்கு"
    assert "diarrhea" in r1["patient_message"]["translated_text"].lower()
    assert "diarrhea" in r1["triage_state"]["main_complaint"].lower()
    assert r1["followup_question_patient"] is not None

    # Step 2: Patient reports duration
    r2 = await triage_service.process_patient_response(sid, "சுமார் ஐந்து மணி நேரம்", "ta")
    assert "5 hours" in r2["triage_state"]["duration"].lower()

    # Step 3: Patient reports severity
    r3 = await triage_service.process_patient_response(sid, "10", "ta")
    assert r3["triage_state"]["severity"] == "10/10"
    assert r3["triage_state"]["priority"] == "high"

    # Step 4: Patient finishes session
    r4 = await triage_service.process_patient_response(sid, "இல்லை", "ta")
    assert r4["is_completed"] is True
    summary = r4["triage_state"]["summary"]
    assert "kishore" in summary.lower()
    assert "diarrhea" in summary.lower()
    assert "5 hours" in summary.lower()
    assert "10/10" in summary
    assert len(r4["messages"]) >= 8
