# Nyaya-Tula AI — Deployment Guide

## Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: v18.x or v20.x
- **OS**: Linux, Windows, macOS

## 1. Local Development Setup

### Backend Setup
```bash
# Create virtual environment
python -m venv .venv
# Activate virtual environment (Windows)
.venv\Scripts\activate
# Activate virtual environment (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:3000
```

## 2. Environment Variables (.env)

```env
# Backend Configuration
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:3000"]

# Optional Multimodal Fallback
GEMINI_API_KEY=""

# OCR Engine
RAPIDOCR_MODEL_PATH=""
```

## 3. Production Deployment

### Docker Deployment
```bash
docker-compose up --build -d
```

### Vercel (Frontend) & Separate Backend (Render/AWS/Cloud Run)
- Frontend is configured in `frontend/` and builds with zero errors via `npm run build`.
- For Vercel deployments, set `NEXT_PUBLIC_BACKEND_URL` to point to your deployed FastAPI backend URL.
