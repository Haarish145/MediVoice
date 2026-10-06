# MediVoice - Cross-Lingual Emergency Triage Voicebot

**Built by Team MediVoice**

MediVoice is a real-time mobile and tablet-friendly emergency intake voicebot. It allows non-English-speaking patients to describe acute symptoms in their preferred regional languages, automatically screens for high-priority red-flag emergencies, and provides a continuously updated English triage summary to the triage nurse via a live, non-refreshing WebSocket interface.

---

## 🌟 Key Features
- **Real-Time Multilingual Patient Intake**: Continuous low-latency speech processing supporting 12 regional Indian languages (Tamil, Hindi, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese) and English.
- **Adaptive Question Engine**: Dynamically identifies missing clinical information (e.g. duration, severity, onset) and asks relevant single follow-up questions in the patient's language.
- **Deterministic Red-Flag Screening Engine**: Evaluates patient symptoms against evidence-based emergency protocols (airway, chest pain, stroke, uncontrolled bleeding) without relying solely on generative LLMs for medical risk flags.
- **Live Nurse Dashboard**: Receives real-time session updates, translated English summaries, red-flag alerts, and original patient transcriptions via WebSocket without browser refresh.
- **Human-in-the-Loop Clinical Safety**: Clear decision-support role with final clinical triage decisions retained by qualified healthcare professionals.

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: React, Vite, Vanilla CSS / clean responsive layout (Mobile-first patient interface, Desktop/tablet nurse dashboard)
- **Backend**: Python 3.15, FastAPI, Uvicorn, WebSockets
- **Database**: SQLite (Development), PostgreSQL-ready
- **Services**: Abstracted interfaces for STT, AI Information Extraction, Translation, and TTS

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js v18+ & npm

### 2. Backend Setup
```bash
# Navigate to project root
cd d:\MediVoice

# Virtual environment created under backend/venv
backend/venv/Scripts/pip install -r backend/requirements.txt

# Run FastAPI Server
backend/venv/Scripts/uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 3. Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Run Vite Dev Server
npm run dev
```

---

## 🧪 Testing
Run backend tests:
```bash
backend/venv/Scripts/python -m pytest backend/app/tests -v
```

---

## 🌐 Cloud & Docker Deployment
MediVoice is production-ready for free cloud deployment:
- **FastAPI + WebSockets Backend**: Deploy on [Render](https://render.com) or [Railway](https://railway.app) (Configured with `render.yaml` & `backend/Dockerfile`)
- **React Frontend**: Deploy on [Vercel](https://vercel.com) (Configured with `vercel.json` & SPA routing)
- **Docker Compose**: Run full-stack anywhere with a single command: `docker compose up -d`
👉 Full step-by-step tutorial: [Production Deployment Guide](docs/deployment.md)


---

## 📜 Documentation
- [Architecture](docs/architecture.md)
- [Real-Time Flow](docs/real-time-flow.md)
- [Red-Flag Rules](docs/red-flag-rules.md)
- [API Specification](docs/api.md)
- [Language Support](docs/languages.md)
- [Testing Guide](docs/testing.md)
- [Deployment Guide](docs/deployment.md)

---

## 🏥 Medical Safety Disclaimer
MediVoice is a communication and decision-support tool. It does not provide medical diagnoses, prescribe treatment, or replace qualified medical personnel.
