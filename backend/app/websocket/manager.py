import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("medivoice.websocket")

class ConnectionManager:
    def __init__(self):
        # session_id -> WebSocket (patient)
        self.patient_connections: Dict[str, WebSocket] = {}
        # session_id -> Set of WebSocket (nurses viewing session)
        self.nurse_session_listeners: Dict[str, Set[WebSocket]] = {}
        # Global nurse connections (nurses viewing all active sessions)
        self.global_nurse_connections: Set[WebSocket] = set()

    async def connect_patient(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.patient_connections[session_id] = websocket
        logger.info(f"Patient connected to session: {session_id}")

    def disconnect_patient(self, session_id: str):
        if session_id in self.patient_connections:
            del self.patient_connections[session_id]
            logger.info(f"Patient disconnected from session: {session_id}")

    async def connect_nurse(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.nurse_session_listeners:
            self.nurse_session_listeners[session_id] = set()
        self.nurse_session_listeners[session_id].add(websocket)
        self.global_nurse_connections.add(websocket)
        logger.info(f"Nurse connected to session: {session_id}")

    def disconnect_nurse(self, session_id: str, websocket: WebSocket):
        if session_id in self.nurse_session_listeners:
            self.nurse_session_listeners[session_id].discard(websocket)
            if not self.nurse_session_listeners[session_id]:
                del self.nurse_session_listeners[session_id]
        self.global_nurse_connections.discard(websocket)
        logger.info(f"Nurse disconnected from session: {session_id}")

    async def send_to_patient(self, session_id: str, event_data: dict):
        if session_id in self.patient_connections:
            ws = self.patient_connections[session_id]
            try:
                await ws.send_json(event_data)
            except Exception as e:
                logger.error(f"Error sending to patient {session_id}: {e}")

    async def broadcast_to_nurse(self, session_id: str, event_data: dict):
        payload = event_data
        # Send to nurses listening specifically to this session
        target_ws_set = set()
        if session_id in self.nurse_session_listeners:
            target_ws_set.update(self.nurse_session_listeners[session_id])
        # Also include global nurse listeners
        target_ws_set.update(self.global_nurse_connections)

        disconnected = []
        for ws in target_ws_set:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.error(f"Error broadcasting to nurse for session {session_id}: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.global_nurse_connections.discard(ws)
            if session_id in self.nurse_session_listeners:
                self.nurse_session_listeners[session_id].discard(ws)

manager = ConnectionManager()
