from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from app.schemas.triage import SessionCreateRequest, MarkSeenRequest
from app.services.triage_service import triage_service
from app.database.connection import sessions_cache, get_db_connection
from app.websocket.manager import manager

router = APIRouter()

def generate_session_id() -> str:
    year = datetime.utcnow().year
    existing_nums = []
    for k in sessions_cache.keys():
        if k.startswith(f"MV-{year}-"):
            parts = k.split("-")
            if parts[-1].isdigit():
                existing_nums.append(int(parts[-1]))
    next_num = max(existing_nums, default=0) + 1
    return f"MV-{year}-{next_num:04d}"

@router.post("/sessions")
def create_session(req: SessionCreateRequest):
    session_id = generate_session_id()
    patient_name = req.patient_name or "Anonymous Patient"
    facility = req.facility or "Emergency Triage Unit"
    session = triage_service.get_or_create_session(
        session_id=session_id,
        language=req.language,
        patient_name=patient_name,
        facility=facility
    )
    return {
        "session_id": session_id,
        "language": req.language,
        "patient_name": patient_name,
        "facility": facility,
        "status": session["status"],
        "created_at": session["created_at"],
        "websocket_patient_url": f"/ws/patient/{session_id}",
        "websocket_nurse_url": f"/ws/nurse/{session_id}"
    }

@router.get("/sessions")
def list_sessions():
    sessions_list = []
    for sid, sdata in sessions_cache.items():
        tstate = sdata.get("triage_state", {})
        sessions_list.append({
            "session_id": sid,
            "language": sdata.get("language", "ta"),
            "patient_name": sdata.get("patient_name") or tstate.get("patient_name") or "Anonymous Patient",
            "facility": sdata.get("facility") or tstate.get("facility") or "Emergency Triage Unit",
            "status": sdata.get("status", "active"),
            "created_at": sdata.get("created_at"),
            "priority": tstate.get("priority", "unknown"),
            "main_complaint": tstate.get("main_complaint"),
            "red_flags": tstate.get("red_flags", []),
            "summary": tstate.get("summary"),
            "is_completed": tstate.get("is_completed", False),
            "seen_at": sdata.get("seen_at") or tstate.get("seen_at"),
            "seen_by": sdata.get("seen_by") or tstate.get("seen_by")
        })
    # Sort with newest sessions first
    sessions_list.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return {"sessions": sessions_list}

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions_cache:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions_cache[session_id]

@router.get("/sessions/{session_id}/summary")
def get_session_summary(session_id: str):
    if session_id not in sessions_cache:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions_cache[session_id]
    tstate = session.get("triage_state", {})
    return {
        "session_id": session_id,
        "language": session.get("language"),
        "patient_name": session.get("patient_name") or tstate.get("patient_name"),
        "facility": session.get("facility") or tstate.get("facility"),
        "priority": tstate.get("priority"),
        "main_complaint": tstate.get("main_complaint"),
        "symptoms": tstate.get("symptoms", []),
        "red_flags": tstate.get("red_flags", []),
        "english_summary": tstate.get("summary"),
        "is_completed": tstate.get("is_completed", False),
        "seen_at": session.get("seen_at") or tstate.get("seen_at"),
        "seen_by": session.get("seen_by") or tstate.get("seen_by")
    }

@router.post("/sessions/{session_id}/seen")
async def mark_session_seen(session_id: str, req: Optional[MarkSeenRequest] = None):
    if session_id not in sessions_cache:
        raise HTTPException(status_code=404, detail="Session not found")
    
    seen_time = datetime.utcnow().isoformat() + "Z"
    nurse_user = (req.nurse_username if req and req.nurse_username else "nurse_admin").strip()

    sessions_cache[session_id]["seen_at"] = seen_time
    sessions_cache[session_id]["seen_by"] = nurse_user

    if "triage_state" in sessions_cache[session_id]:
        sessions_cache[session_id]["triage_state"]["seen_at"] = seen_time
        sessions_cache[session_id]["triage_state"]["seen_by"] = nurse_user

    # Broadcast seen event to all nurses viewing dashboard
    await manager.broadcast_to_nurse(session_id, {
        "event": "session_seen",
        "session_id": session_id,
        "data": {
            "session_id": session_id,
            "seen_at": seen_time,
            "seen_by": nurse_user
        }
    })

    return {
        "status": "success",
        "session_id": session_id,
        "seen_at": seen_time,
        "seen_by": nurse_user
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id not in sessions_cache:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions_cache[session_id]

    # Also clean up from SQLite DB if exists
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patient_sessions WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM triage_assessments WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM red_flag_events WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Notify nurses listening
    await manager.broadcast_to_nurse(session_id, {
        "event": "session_deleted",
        "session_id": session_id,
        "data": {"session_id": session_id}
    })

    return {
        "status": "deleted",
        "session_id": session_id
    }
