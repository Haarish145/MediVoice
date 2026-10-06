import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.api.routes import health, languages, sessions, auth, tts
from app.websocket import patient, nurse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medivoice")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Multilingual Emergency Triage Voicebot API"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(languages.router, prefix=settings.API_PREFIX, tags=["Languages"])
app.include_router(sessions.router, prefix=settings.API_PREFIX, tags=["Sessions"])
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["Authentication"])
app.include_router(tts.router, prefix=settings.API_PREFIX, tags=["Text to Speech"])

# Include WebSocket Routers
app.include_router(patient.router, tags=["Patient WebSocket"])
app.include_router(nurse.router, tags=["Nurse WebSocket"])

@app.get("/health", tags=["Health"], include_in_schema=False)
@app.get("/healthz", tags=["Health"], include_in_schema=False)
def root_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE
    }

@app.on_event("startup")
async def startup_event():
    logger.info(f"MediVoice Backend v{settings.VERSION} starting...")
    logger.info(f"Demo Mode: {settings.DEMO_MODE}")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MediVoice API</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 2.5rem; max-width: 520px; width: 90%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
    .icon { font-size: 3rem; margin-bottom: 1rem; }
    h1 { font-size: 1.8rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.4rem; }
    .version { font-size: 0.8rem; background: #0ea5e9; color: white; padding: 0.2rem 0.7rem; border-radius: 20px; display: inline-block; margin-bottom: 1rem; }
    p { color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem; }
    .links { display: flex; flex-direction: column; gap: 0.75rem; }
    a { display: block; padding: 0.75rem 1rem; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: opacity 0.2s; }
    a:hover { opacity: 0.85; }
    .btn-primary { background: #0ea5e9; color: white; }
    .btn-secondary { background: #1d4ed8; color: white; }
    .btn-outline { background: transparent; border: 1px solid #475569; color: #94a3b8; }
    .status { margin-top: 1.5rem; font-size: 0.78rem; color: #22c55e; }
    .dot { display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 6px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">🏥</div>
    <h1>MediVoice API</h1>
    <span class="version">v1.0.0 &nbsp;•&nbsp; Demo Mode</span>
    <p>Real-Time Multilingual Emergency Triage Voicebot Backend.<br/>The patient-facing app runs on the frontend server.</p>
    <div class="links">
      <a class="btn-primary" href="http://localhost:5173" target="_blank">🚀 Open MediVoice App (localhost:5173)</a>
      <a class="btn-secondary" href="/docs" target="_blank">📖 Interactive API Docs (Swagger)</a>
      <a class="btn-outline" href="/api/health" target="_blank">❤️ Health Check</a>
    </div>
    <div class="status"><span class="dot"></span>Backend is running on port 8000</div>
  </div>
</body>
</html>"""
