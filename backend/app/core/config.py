import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediVoice"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Cors
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]
    
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
