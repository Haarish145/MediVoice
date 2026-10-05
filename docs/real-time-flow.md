# Real-Time Flow Documentation

## Overview
MediVoice avoids batch record-and-upload workflows in favor of a genuinely real-time streaming pipeline over persistent WebSockets.

## Detailed Data & Event Flow

1. **Session Initialization**:
   - Patient opens interface, selects language, creates session (`MV-YYYY-NNNN`).
   - Patient connects to `/ws/patient/{session_id}`.
   - Nurse connects to `/ws/nurse/{session_id}` or global nurse channel.

2. **Patient Speech Processing**:
   - Patient speaks into browser microphone.
   - Speech chunks / partial audio or text transcripts are transmitted over WebSocket (`patient_speech_partial` / `patient_speech_final`).
   - Backend processes incoming speech using low-latency Speech-to-Text service.

3. **Triage State Update & Information Extraction**:
   - AI/NLP extractor analyzes transcribed text.
   - Main complaint, symptoms, onset, duration, severity, and associated symptoms are extracted into structured JSON state.
   - Missing information is identified by adaptive question engine.

4. **Red-Flag Screening**:
   - Screening engine evaluates updated triage state against rule bank.
   - If a high-acuity condition is met (e.g. severe chest pain + dyspnea), a `red_flag_detected` event is triggered immediately.

5. **Nurse Dashboard Broadcast**:
   - Backend broadcasts `triage_state_updated`, `nurse_dashboard_update`, and `red_flag_detected` to active nurse WebSocket sessions.
   - Nurse dashboard updates UI immediately without requiring a page refresh.
