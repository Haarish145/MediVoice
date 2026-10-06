import os
import json
from typing import List, Union

def parse_origins(val: Union[str, List[str], None]) -> List[str]:
    if not val:
        return ["http://localhost:5173", "http://127.0.0.1:5173", "https://*.vercel.app", "*"]
    if isinstance(val, list):
        return val
    val = str(val).strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return [origin.strip() for origin in val.split(",") if origin.strip()]

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "MediVoice")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    
    # Cors
    ALLOWED_ORIGINS: List[str] = parse_origins(os.getenv("ALLOWED_ORIGINS"))
    
    # Secrets & Mode
    JWT_SECRET: str = os.getenv("JWT_SECRET", "medivoice-hackathon-secret-key-change-in-production-2026")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    # Service Keys (Backend Only)
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    SPEECH_API_KEY: str = os.getenv("SPEECH_API_KEY", "")
    TRANSLATION_API_KEY: str = os.getenv("TRANSLATION_API_KEY", "")
    TTS_API_KEY: str = os.getenv("TTS_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medivoice.db")

settings = Settings()
