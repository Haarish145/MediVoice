import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

def get_allowed_origins() -> list[str]:
    origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if origins_env:
        return [origin.strip() for origin in origins_env.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173", "https://*.vercel.app", "*"]

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediVoice"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Cors
    ALLOWED_ORIGINS: list[str] = get_allowed_origins()
    
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

