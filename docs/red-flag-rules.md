# Red-Flag Screening Rules & Framework

## Medical Disclaimer & Principles
MediVoice is a communication and decision-support screening tool for triage nurses. It **does not** provide autonomous diagnoses, prescribe medication, or replace qualified medical staff.

## Rule Categories & Reference Framework

Rules are based on standardized emergency triage protocols (e.g. Emergency Severity Index / Manchester Triage system principles):

1. **Airway & Breathing Concerns (`HIGH_PRIORITY_BREATHING`)**:
   - Symptoms: Severe shortness of breath, inability to speak full sentences, acute dyspnea.
   - Priority: HIGH / RED.

2. **Cardiovascular / Circulation (`HIGH_PRIORITY_CHEST_PAIN`)**:
   - Symptoms: Acute chest pain, pressure/tightness with radiation or dyspnea.
   - Priority: HIGH / RED.

3. **Neurological / Altered Mental Status (`HIGH_PRIORITY_NEURO`)**:
   - Symptoms: Sudden weakness, facial drooping, speech difficulty, sudden confusion.
   - Priority: HIGH / RED.

4. **Severe Uncontrolled Bleeding / Trauma (`HIGH_PRIORITY_TRAUMA`)**:
   - Symptoms: Heavy bleeding, penetrating injuries, severe acute pain (>8/10).
   - Priority: HIGH / RED.

## Auditability
Each triggered rule outputs structured explanation fields:
- `rule_id`: Unique identifier (e.g., `HIGH_PRIORITY_BREATHING`)
- `rule_name`: Human-readable name
- `priority`: `high` | `medium` | `low` | `unknown`
- `triggered_symptoms`: Array of extracted symptoms that matched
- `reason`: Explanation string for triage nurse
- `timestamp`: ISO-8601 timestamp
- `reference`: Clinical protocol reference
