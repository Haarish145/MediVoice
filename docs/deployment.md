# 🚀 MediVoice Production Deployment Guide

MediVoice consists of:
- **Backend**: FastAPI with async WebSockets for real-time patient-nurse communication.
- **Frontend**: Vite + React Single Page Application (SPA) with microphone Web Speech API & TTS audio playback.
- **Database**: SQLite (persisted via local volume or disk) or PostgreSQL-ready.

---

## 🌟 Recommended Free Cloud Architecture

| Component | Recommended Host | Free Tier Benefits | Protocol |
| :--- | :--- | :--- | :--- |
| **Backend API & WebSockets** | [Render](https://render.com) or [Railway](https://railway.app) | Native WebSocket (`wss://`) support, automatic SSL, background worker support | `https://` & `wss://` |
| **Frontend Web App** | [Vercel](https://vercel.com) | Global edge CDN, automated Git preview deployments, custom domains | `https://` |

---

## 📋 Pre-Deployment Checklist

1. [x] Push your latest code to a Git repository (e.g., GitHub).
2. [x] Note your repository URL (e.g., `https://github.com/your-username/MediVoice`).
3. [x] Microphones require HTTPS in browsers: Both Render and Vercel provide free SSL automatically.

---

## Option 1: Render (Backend) + Vercel (Frontend) [Recommended]

### Step 1: Deploy Backend on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `MediVoice` repository.
4. Configure the Web Service settings:
   - **Name**: `medivoice-backend` (or your choice)
   - **Region**: Choose closest to your users (e.g., Singapore, Frankfurt, Oregon)
   - **Root Directory**: `backend` *(or leave blank if using root)*
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt` (or `pip install -r backend/requirements.txt` if root is blank)
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips "*"
     ```
     *(If Root Directory is left blank at repo root, use: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips "*"`)*
   - **Plan**: `Free`
5. In **Advanced** > **Add Environment Variables**:
   - `DEMO_MODE` = `true`
   - `JWT_SECRET` = *(Click Generate or enter a secure random 32-char string)*
   - `ALLOWED_ORIGINS` = `https://*.vercel.app,http://localhost:5173`
   - `DATABASE_URL` = `sqlite:///./medivoice.db`
6. Click **Deploy Web Service**.
7. Once deployed, copy your backend URL:
   - **Example**: `https://medivoice-backend.onrender.com`
   - Verify it by opening `https://medivoice-backend.onrender.com/health` in your browser. You should see `{"status":"ok", ...}`.

---

### Step 2: Deploy Frontend on Vercel

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import your `MediVoice` Git repository.
4. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend` (Alternatively, the included root `vercel.json` will auto-detect).
5. Open **Environment Variables** and add:
   - **Key**: `VITE_BACKEND_URL`
   - **Value**: `https://medivoice-backend.onrender.com` *(use your actual Render backend URL without trailing slash)*
   - *(Optional)* **Key**: `VITE_WS_URL`
   - **Value**: `wss://medivoice-backend.onrender.com` *(if omitted, the app will automatically convert https:// to wss://)*
6. Click **Deploy**.
7. In ~60 seconds, your application will be live at `https://medivoice.vercel.app`!

---

### Step 3: Update Backend Allowed Origins (CORS)

Once Vercel gives you your production URL (e.g. `https://medivoice-xyz.vercel.app`):
1. Go back to your [Render Dashboard](https://dashboard.render.com) > your backend service > **Environment**.
2. Update `ALLOWED_ORIGINS`:
   ```
   https://medivoice-xyz.vercel.app,https://*.vercel.app,http://localhost:5173
   ```
3. Save changes. Render will automatically redeploy with the updated CORS policy.

---

## Option 2: Deploy Backend on Railway

1. Go to [Railway.app](https://railway.app) and click **New Project** > **Deploy from GitHub repo**.
2. Select your repository.
3. In service **Settings**:
   - Set **Root Directory** to `/backend`.
   - Railway auto-detects `requirements.txt` and `Procfile`.
4. In service **Variables**:
   - Add `DEMO_MODE=true`
   - Add `JWT_SECRET=your-secret-key`
   - Add `ALLOWED_ORIGINS=https://*.vercel.app,http://localhost:5173`
5. In **Settings** > **Networking**, click **Generate Domain** (e.g. `medivoice-backend.up.railway.app`).
6. Point your Vercel frontend `VITE_BACKEND_URL` to this Railway domain.

---

## Option 3: Docker & Docker Compose (Self-Hosted / VPS / Local)

If deploying to your own Linux server (Ubuntu, Debian, EC2, Droplet) or running locally:

### 1. Prerequisites
- Docker & Docker Compose installed:
  ```bash
  sudo apt update && sudo apt install -y docker.io docker-compose-v2
  ```

### 2. Clone and Launch
```bash
git clone https://github.com/your-username/MediVoice.git
cd MediVoice

# Build and start all services in background
docker compose up -d --build
```

### 3. Verify
- **Frontend App**: `http://<your-server-ip>:3000`
- **Backend API**: `http://<your-server-ip>:8000`
- **Backend Health Check**: `http://<your-server-ip>:8000/health`
- **Interactive Swagger Docs**: `http://<your-server-ip>:8000/docs`

---

## ⚙️ Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port for the Uvicorn server (auto-injected on Render/Railway). |
| `DEMO_MODE` | `true` | Allows full simulated STT, AI extraction & red flags without external paid API keys. |
| `ALLOWED_ORIGINS` | `*` | Comma-separated allowed frontend domains for CORS. |
| `DATABASE_URL` | `sqlite:///./medivoice.db` | SQLite database file location or PostgreSQL connection string. |
| `JWT_SECRET` | *(Demo key)* | Secret key used to sign nurse authentication tokens. |
| `AI_API_KEY` | *(Optional)* | Custom LLM API key if replacing demo extraction engine. |
| `TTS_API_KEY` | *(Optional)* | Custom TTS API key if using cloud voice generation. |

### Frontend (`frontend/.env.production`)
| Variable | Example | Description |
| :--- | :--- | :--- |
| `VITE_BACKEND_URL` | `https://medivoice-backend.onrender.com` | Base URL of deployed FastAPI backend. |
| `VITE_WS_URL` | `wss://medivoice-backend.onrender.com` | Base URL for WebSocket connections (auto-derived if omitted). |

---

## 🔍 Verification & Testing Live Deployment

1. **Verify Backend**:
   - Visit `https://<backend-url>/health`
   - Expect: `{"status":"ok", "service":"MediVoice", ...}`
2. **Verify Frontend**:
   - Open `https://<frontend-url>` on Chrome (Desktop or Android phone/tablet).
   - Click **Start Voice Intake**.
   - Grant microphone permission when prompted.
   - Speak a symptom in Tamil or English (or choose quick-sample prompt).
   - In a second browser tab, log in to Nurse Portal (`/nurse`) with demo credentials (`nurse` / `emergency123`).
   - Confirm that the live patient transcript, red flag alarms, and English triage card stream instantly across the WebSocket connection without refreshing!
