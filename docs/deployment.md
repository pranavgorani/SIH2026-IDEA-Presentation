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

### Vercel (Frontend) & Cloud Backend (Render / Docker / Railway)
- **Frontend Root Directory**: `frontend` (Auto-detected as Next.js framework).
- **Production Environment Variables** in Vercel (`Project Settings → Environment Variables`):

| Variable Name | Environment | Vercel Visibility | Value | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `BACKEND_API_URL` | Production, Preview | **Sensitive / Secret** | `https://<your-backend-name>.onrender.com` | **Authoritative Server-Side Variable.** Required. Used by Next.js reverse proxy (`/api/backend/*`) and `/api/screen`. |
| `GEMINI_API_KEY` | Production, Preview | **Sensitive / Secret** | `AIzaSy...` | Optional server-side multimodal vision fallback. Never exposed to browser. |
| `NEXT_PUBLIC_API_URL` | None / Optional | **Plaintext / Config** | *(Leave empty)* | **DO NOT set to Secret.** If set at all, Vercel requires Config/Plaintext visibility. Not needed because Next.js proxies calls. |

> [!WARNING]
> **Vercel Visibility Error Prevention**:
> Never mark any variable starting with `NEXT_PUBLIC_` as "Secret" in Vercel. Vercel rejects Secret visibility on `NEXT_PUBLIC_` because public variables are inlined into client-side JS bundles. Use `BACKEND_API_URL` instead, which is server-side and fully supports Secret visibility.
>
> **No Placeholders in Production**:
> Never use `http://localhost:8000`, `127.0.0.1`, or template placeholders like `<your-render-url>`. Vercel serverless functions run in the cloud and cannot reach your local machine. Deploy your backend to Render/Railway first, then copy the live HTTPS URL.

