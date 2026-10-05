# MediVoice Architecture Overview

## System Architecture

MediVoice is a real-time, cross-lingual emergency intake voicebot and triage support application built by **Team MediVoice**.

```
+------------------+         WebSocket (/ws/patient/{id})        +---------------------+
|  Patient Browser | <-----------------------------------------> |   FastAPI Backend   |
| (React/Vite App) |                                             | (WebSocket Manager) |
+------------------+                                             +----------+----------+
                                                                            |
+------------------+         WebSocket (/ws/nurse/{id})             |
| Nurse Dashboard  | <----------------------------------------------+
| (React/Vite App) | (Real-Time Live Updates without Refresh)
+------------------+
```

## Key Components

1. **Frontend (React + Vite)**
   - **Patient Interface**: Mobile/tablet-friendly intake interface with language selection, microphone controls, live transcription area, and adaptive follow-up questions.
   - **Nurse Dashboard**: Desktop/tablet interface showing active intake sessions, real-time updated English summaries, red-flag emergency alerts, and original patient transcriptions.

2. **Backend (FastAPI + Uvicorn)**
   - **Connection Manager**: Manages concurrent WebSocket connections for patient and nurse sessions, mapping active `session_id`s and broadcasting real-time events.
   - **Conversation Engine**: Maintains structured triage state per session (`main_complaint`, `symptoms`, `onset`, `duration`, `severity`, `associated_symptoms`, `uncertainties`, `contradictions`).
   - **Red-Flag Screening Engine**: Deterministic screening engine implementing structured medical rules (airway, breathing, circulation, altered mental status, severe pain).
   - **Service Layer**: Pluggable abstraction for Speech Recognition (STT), AI information extraction, Translation, and Text-To-Speech (TTS).

3. **Database**
   - SQLite for lightweight development persistence (session metadata, conversation logs, red flag events, triage state).
   - PostgreSQL-ready schema design for production deployment.
