import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings

# Lightweight SQLite database persistence & in-memory session manager
DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def init_db():
    if DB_PATH.startswith(":memory:"):
        conn = sqlite3.connect(":memory:", check_same_thread=False)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_sessions (
        session_id TEXT PRIMARY KEY,
        language TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        speaker TEXT NOT NULL,
        original_text TEXT NOT NULL,
        translated_text TEXT,
        message_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES patient_sessions(session_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS triage_assessments (
        session_id TEXT PRIMARY KEY,
        main_complaint TEXT,
        symptoms TEXT,
        onset TEXT,
        duration TEXT,
        severity TEXT,
        location TEXT,
        associated_symptoms TEXT,
        relevant_history TEXT,
        uncertainties TEXT,
        contradictions TEXT,
        summary TEXT,
        priority TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES patient_sessions(session_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS red_flag_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        rule_id TEXT NOT NULL,
        priority TEXT NOT NULL,
        reason TEXT NOT NULL,
        triggered_symptoms TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES patient_sessions(session_id)
    )
    """)
    
    conn.commit()
    conn.close()

# Run DB initialization
init_db()

# Active in-memory session cache for fast real-time access
sessions_cache: Dict[str, Dict[str, Any]] = {}

def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
