# Production Deployment Guide

## Overview
MediVoice is designed for containerized deployment with FastAPI (Uvicorn backend) and static React build (served via Nginx or Cloudflare Pages/Vercel) over Secure WebSockets (`wss://`).

## Production Requirements
- HTTPS/WSS Termination
- PostgreSQL Database
- Environment Variables configured safely (never commit `.env`)
- CORS origins restricted to authorized domain

## Running with Uvicorn
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
