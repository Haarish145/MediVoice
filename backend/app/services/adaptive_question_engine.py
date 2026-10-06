import logging
from typing import Dict, Any, Optional, Tuple
from app.schemas.triage import TriageState
from app.services.translation_service import translation_service

logger = logging.getLogger("medivoice.adaptive_question")

class AdaptiveQuestionEngine:
    async def generate_next_question(
        self,
        triage_state: TriageState,
        force_question_type: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Determines missing triage information and generates ONE relevant follow-up question.
        Ensures questions are NEVER repeated once answered (tracked in asked_questions).
        Supports forced question types (e.g., additional_symptoms_prompt, duration, or completion_check).
        Once all clinical questions are answered or asked, asks the completion check question:
        "Do you have any other symptoms or problems, or can we complete the intake session?"
        """
        if triage_state.is_completed:
            return None, None, None

        language = triage_state.language or "ta"

        # 1. Handle explicit forced question type
        if force_question_type:
            next_type = force_question_type
            if next_type == "additional_symptoms_prompt":
                question_en = "Please describe what other symptoms or problems you are experiencing."
            elif next_type == "completion_check":
                question_en = "Do you have any other symptoms or problems, or can we complete the intake session?"
            elif next_type == "additional_duration":
                question_en = "How long have you been experiencing these symptoms?"
            elif next_type == "additional_severity":
                question_en = "How severe is your discomfort on a scale of 1 to 10?"
            elif next_type == "duration":
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

        # 2. Check clinical questions that still have missing information
        missing = triage_state.missing_information or []

        if missing:
            next_type = missing[0]
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

        # 3. When all specific clinical questions have been answered, ask the completion check
        next_type = "completion_check"
        question_en = "Do you have any other symptoms or problems, or can we complete the intake session?"
        question_patient = await translation_service.translate_question(
            question_en=question_en,
            target_language=language,
            question_type=next_type
        )
        return question_en, question_patient, next_type

adaptive_question_engine = AdaptiveQuestionEngine()
