import pytest
from unittest.mock import patch
from app.services.triage_service import triage_service
from app.services.translation_service import translation_service

@pytest.mark.asyncio
async def test_burn_wound_offline_and_triage_flow():
    """
    Validates that patient speaking Tamil regarding severe burn on hand:
    'ஆம் எனக்கு கையில் தீக்காயம் பட்டு உள்ளது மிகக் கடுமையாக வலிக்கிறது'
    1. Is accurately translated into clinical English (never truncated to 'I have').
    2. Identifies burn injury, location 'hand', and severity 'severe'.
    3. Triggers Acute Burn Red Flag warning.
    4. Accurately captures additional complaints and generates a professional summary.
    """
    session_id = "test_burn_session_001"
    session = triage_service.get_or_create_session(session_id, language="ta", patient_name="Ramesh")

    # Simulate completion check was the last question asked
    session["last_question_type"] = "completion_check"

    burn_text = "ஆம் எனக்கு கையில் தீக்காயம் பட்டு உள்ளது மிகக் கடுமையாக வலிக்கிறது"

    # Test under offline conditions (datacenter cloud IP fallback)
    with patch.object(translation_service, "_online_translate", return_value=None):
        res1 = await triage_service.process_patient_response(session_id, burn_text, language="ta")

        # 1. Translation check
        trans = res1["patient_message"]["translated_text"]
        assert "burn" in trans.lower(), f"Expected burn in translation, got: {trans}"
        assert "hand" in trans.lower(), f"Expected hand in translation, got: {trans}"
        assert trans != "I have", "Translation must not be truncated to 'I have'"

        # 2. State & symptom extraction check
        t_state = res1["triage_state"]
        assert "burn" in t_state.get("main_complaint", "").lower() or any("burn" in s.lower() for s in t_state.get("symptoms", []))
        assert t_state.get("location") == "hand"
        assert t_state.get("severity") in ["severe", "10/10", "extreme"]

        # 3. Red flag check
        flags = [rf["rule_id"] for rf in res1["red_flags"]]
        assert "HIGH_PRIORITY_ACUTE_BURN_TRAUMA" in flags

        # 4. Next question prompted should be duration
        assert res1["followup_question_patient"] is not None
        assert not res1["is_completed"]

        # 5. Provide duration
        res2 = await triage_service.process_patient_response(session_id, "20 நிமிடங்கள்", language="ta")
        summary = res2["triage_state"].get("summary", "")
        assert "burn" in summary.lower()
        assert "hand" in summary.lower()
