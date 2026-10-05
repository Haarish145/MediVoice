import logging
from typing import Dict, Any, Optional, Tuple
from app.schemas.triage import TriageState
from app.services.translation_service import translation_service

logger = logging.getLogger("medivoice.adaptive_question")

class AdaptiveQuestionEngine:
    async def generate_next_question(self, triage_state: TriageState) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Determines missing triage information and generates ONE relevant follow-up question.
        Ensures questions are NEVER repeated once answered (tracked in asked_questions).
        Once all clinical questions are answered or asked, asks the completion check question:
        "Do you have any other problems or can we complete the intake session?"
        If the completion_check has already been asked but patient didn't trigger completion,
        it re-asks the completion question (loop prevention).
        Returns: (english_question, patient_language_question, missing_info_type)
        """
        if triage_state.is_completed:
            return None, None, None

        missing = triage_state.missing_information or []
        asked = set(triage_state.asked_questions or [])
        language = triage_state.language or "ta"

        # 1. Filter out questions that have already been asked
        unasked = [m for m in missing if m not in asked]

        if unasked:
            next_type = unasked[0]
            question_en = ""

            if next_type == "duration":
                question_en = "How long have you been experiencing these symptoms?"
            elif next_type == "severity":
                question_en = "How severe is your discomfort on a scale of 1 to 10?"
            elif next_type == "breathing_difficulty":
                question_en = "Are you experiencing any difficulty breathing or shortness of breath?"
            elif next_type == "onset":
                question_en = "Did these symptoms start suddenly or gradually?"
            else:
                question_en = "Can you describe any other symptoms you are experiencing?"

            question_patient = await translation_service.translate_question(
                question_en=question_en,
                target_language=language,
                question_type=next_type
            )
            return question_en, question_patient, next_type

        # 2. When all specific clinical questions have been answered, ask the completion check
        # This will be re-asked every turn until the patient either confirms completion
        # or introduces a new symptom that triggers more questions.
        next_type = "completion_check"
        question_en = "Do you have any other symptoms or problems, or can we complete the intake session?"
        question_patient = await translation_service.translate_question(
            question_en=question_en,
            target_language=language,
            question_type=next_type
        )
        return question_en, question_patient, next_type

adaptive_question_engine = AdaptiveQuestionEngine()
