import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.websocket.events import EventTypes
from app.services.triage_service import triage_service

logger = logging.getLogger("medivoice.websocket.patient")
router = APIRouter()

@router.websocket("/ws/patient/{session_id}")
async def patient_websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect_patient(session_id, websocket)
    
    # Notify patient of successful connection
    try:
        await websocket.send_json({
            "event": EventTypes.CONNECTION,
            "session_id": session_id,
            "data": {"status": "connected", "role": "patient"}
        })
        
        # Broadcast initial session start to nurse
        await manager.broadcast_to_nurse(session_id, {
            "event": EventTypes.SESSION_STARTED,
            "session_id": session_id,
            "data": {"status": "active"}
        })
    except Exception as e:
        logger.error(f"Error initializing patient websocket {session_id}: {e}")
        manager.disconnect_patient(session_id)
        return

    try:
        while True:
            try:
                raw_data = await websocket.receive_text()
            except (WebSocketDisconnect, RuntimeError):
                break

            if not raw_data:
                break

            try:
                message = json.loads(raw_data)
            except Exception:
                message = {"event": EventTypes.PATIENT_SPEECH_FINAL, "data": {"text": raw_data, "language": "ta"}}

            event_type = message.get("event", EventTypes.PATIENT_SPEECH_FINAL)
            payload = message.get("data", {})
            patient_text = payload.get("text", "")
            language = payload.get("language", "ta")

            if not patient_text:
                continue

            # Notify patient that processing has started
            await websocket.send_json({
                "event": EventTypes.AI_PROCESSING,
                "session_id": session_id,
                "data": {"status": "processing"}
            })

            # Process response through triage engine
            result = await triage_service.process_patient_response(
                session_id=session_id,
                patient_text=patient_text,
                language=language
            )

            # Respond to Patient
            await websocket.send_json({
                "event": EventTypes.TRIAGE_STATE_UPDATED,
                "session_id": session_id,
                "data": {
                    "triage_state": result["triage_state"],
                    "followup_question": result["followup_question_patient"],
                    "patient_message": result["patient_message"],
                    "messages": result["messages"],
                    "is_completed": result.get("is_completed", False)
                }
            })

            # Real-time Broadcast to Nurse Dashboard (NO REFRESH REQUIRED!)
            nurse_update_payload = {
                "event": EventTypes.NURSE_DASHBOARD_UPDATE,
                "session_id": session_id,
                "data": {
                    "session_id": session_id,
                    "language": language,
                    "status": "completed" if result.get("is_completed") else "active",
                    "triage_state": result["triage_state"],
                    "patient_message": result["patient_message"],
                    "red_flags": result["red_flags"],
                    "summary": result["triage_state"].get("summary"),
                    "messages": result["messages"],
                    "is_completed": result.get("is_completed", False)
                }
            }
            await manager.broadcast_to_nurse(session_id, nurse_update_payload)

            # If intake complete, notify patient
            if result.get("is_completed"):
                await websocket.send_json({
                    "event": "session_completed",
                    "session_id": session_id,
                    "data": {
                        "status": "completed",
                        "triage_state": result["triage_state"],
                        "summary": result["triage_state"].get("summary")
                    }
                })

            # If Red Flag triggered, broadcast immediate emergency alert event to Nurse
            if result["red_flags"]:
                await manager.broadcast_to_nurse(session_id, {
                    "event": EventTypes.RED_FLAG_DETECTED,
                    "session_id": session_id,
                    "data": {
                        "red_flags": result["red_flags"],
                        "priority": "high",
                        "reason": "Possible high-priority symptoms detected. Nurse review required."
                    }
                })

    except Exception as e:
        logger.error(f"WebSocket error on patient channel {session_id}: {e}")
    finally:
        manager.disconnect_patient(session_id)
        logger.info(f"Patient WebSocket disconnected for session {session_id}")
        await manager.broadcast_to_nurse(session_id, {
            "event": EventTypes.SESSION_ENDED,
            "session_id": session_id,
            "data": {"status": "disconnected"}
        })
