# MediVoice API Specification

## REST Endpoints

### Health Check
- **GET** `/api/health`
- **Response**: `{"status": "ok", "service": "MediVoice Backend", "version": "1.0.0"}`

### Language Configuration
- **GET** `/api/languages`
- **Response**: Array of supported language objects (`code`, `display_name`, `locale`, etc.).

### Session Management
- **POST** `/api/sessions`
  - **Body**: `{"language": "ta"}`
  - **Response**: `{"session_id": "MV-2026-0001", "status": "active", "language": "ta", "created_at": "..."}`
- **GET** `/api/sessions/{session_id}`
  - **Response**: Full session metadata and triage state.
- **GET** `/api/sessions/{session_id}/summary`
  - **Response**: English triage summary and red-flag alerts.
- **GET** `/api/sessions/{session_id}/messages`
  - **Response**: Conversation transcript history.

### Nurse Authentication
- **POST** `/api/auth/nurse/login`
  - **Body**: `{"username": "nurse_admin", "password": "..."}`
  - **Response**: `{"access_token": "...", "token_type": "bearer"}`

## WebSocket Endpoints

- **Patient Channel**: `ws://localhost:8000/ws/patient/{session_id}`
- **Nurse Channel**: `ws://localhost:8000/ws/nurse/{session_id}`

### Event Payload Structure
```json
{
  "event": "patient_speech_final",
  "session_id": "MV-2026-0001",
  "data": {
    "text": "எனக்கு திடீரென்று மார்பில் வலி...",
    "language": "ta"
  },
  "timestamp": "2026-10-05T08:00:00Z"
}
```
