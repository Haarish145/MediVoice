import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.websocket.events import EventTypes
from app.database.connection import sessions_cache

logger = logging.getLogger("medivoice.websocket.nurse")
router = APIRouter()

@router.websocket("/ws/nurse/{session_id}")
async def nurse_websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect_nurse(session_id, websocket)
    
    # Send initial snapshot of session state if available
    session_data = sessions_cache.get(session_id)
    initial_payload = {
        "event": EventTypes.CONNECTION,
        "session_id": session_id,
        "data": {
            "status": "connected",
            "role": "nurse",
            "session_snapshot": session_data
        }
    }
    try:
        await websocket.send_json(initial_payload)
    except Exception as e:
        logger.error(f"Error sending nurse init payload for session {session_id}: {e}")
        manager.disconnect_nurse(session_id, websocket)
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
                msg = json.loads(raw_data)
                cmd = msg.get("command")
                if cmd == "get_snapshot":
                    snap = sessions_cache.get(session_id)
                    await websocket.send_json({
                        "event": EventTypes.NURSE_DASHBOARD_UPDATE,
                        "session_id": session_id,
                        "data": snap
                    })
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Nurse WebSocket error on session {session_id}: {e}")
    finally:
        manager.disconnect_nurse(session_id, websocket)
        logger.info(f"Nurse WebSocket disconnected from session {session_id}")
