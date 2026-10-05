# MediVoice Testing Guide

## Automated Backend Testing
Run pytest from the backend environment:
```bash
python -m pytest backend/app/tests -v
```

## Mandatory Real-Time Acceptance Test Plan

1. Open Patient Interface in Browser Window 1 (`http://localhost:5173`)
2. Open Nurse Dashboard in Browser Window 2 (`http://localhost:5173/nurse`)
3. Select Tamil language on Patient Interface and start intake session (`MV-2026-0001`).
4. Nurse Dashboard connects to the same session `MV-2026-0001`.
5. Speak or send Tamil patient symptom payload ("எனக்கு திடீரென்று மார்பில் வலி").
6. Verify:
   - Live transcript updates in Patient Interface.
   - Nurse Dashboard receives live symptom update without browser refresh.
   - Red-Flag screening runs and alerts nurse if high-priority criteria are met.
