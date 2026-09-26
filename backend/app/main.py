import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Configure Python search path for both monorepo root and backend root
_current_file = Path(__file__).resolve()
_app_dir = _current_file.parent
_backend_dir = _app_dir.parent
_workspace_dir = _backend_dir.parent

for _p in [str(_workspace_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from backend.app.core.config import settings
from backend.app.models.database import init_db, SessionLocal
from backend.app.api.auth import router as auth_router, seed_demo_users_if_needed
from backend.app.api.screening import router as screening_router
from backend.app.api.cases import router as cases_router
from backend.app.api.documents import router as documents_router
from backend.app.api.audit import router as audit_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.settings import router as settings_router
from backend.app.api.reports import router as reports_router
from backend.app.services.synthetic_generator import synthetic_generator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables & demo seed data
    try:
        init_db()
        db = SessionLocal()
        try:
            seed_demo_users_if_needed(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Notice: Database initialization: {e}")

    # Pre-render synthetic demonstration cases so demo mode works out of the box
    try:
        synthetic_generator.generate_all_presets()
    except Exception as e:
        print(f"Notice: Synthetic document initialization: {e}")

    yield
    # Shutdown logic if needed

# FastAPI Application Instance
app = FastAPI(
    title=settings.PROJECT_TITLE,
    description="""
# TRUST-ID — AI-Powered Fake Identity & Document Screening System
**Smart India Hackathon 2026 Prototype (Problem ID: SIH26188)**
**Ministry of Home Affairs / Blockchain & Cybersecurity / Software**

### Core Capabilities:
- **Scan**: Modular OCR and ICAO 9303 MRZ extraction with check-digit verification.
- **Detect**: Computer Vision Error Level Analysis (ELA), high-frequency noise variance, and forensic heatmaps.
- **Validate**: Chronological logic, expiry enforcement, and cross-field consistency.
- **Identity**: Biometric 1:1 facial portrait comparison and quality checking.
- **Records**: Simulated issuer database adapter architecture.
- **Score**: Multi-signal explainable risk fusion (0–100) with safety-first human escalation.
- **Audit**: Tamper-evident SHA-256 cryptographic hash chain ledger.
    """,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under both /api and /api/backend for Vercel Services compatibility
for route_prefix in ["/api", "/api/backend"]:
    app.include_router(auth_router, prefix=route_prefix)
    app.include_router(screening_router, prefix=route_prefix)
    app.include_router(cases_router, prefix=route_prefix)
    app.include_router(documents_router, prefix=route_prefix)
    app.include_router(audit_router, prefix=route_prefix)
    app.include_router(analytics_router, prefix=route_prefix)
    app.include_router(settings_router, prefix=route_prefix)
    app.include_router(reports_router, prefix=route_prefix)

from backend.app.providers.gemini_provider import gemini_provider
from sqlalchemy import text

# Standard Health Endpoints
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.get("/api/backend/health", tags=["Health"])
def health():
    # Database check
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        db_status = "offline"

    # OpenCV check
    try:
        import cv2
        opencv_status = "online"
    except Exception:
        opencv_status = "offline"

    # Gemini check
    gemini_status = "configured" if gemini_provider.is_configured else "unconfigured"

    # Storage check
    storage_status = "online" if settings.STORAGE_DIR.exists() else "offline"

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "services": {
            "database": db_status,
            "ocr": "online",
            "opencv": opencv_status,
            "gemini": gemini_status,
            "storage": storage_status
        }
    }

@app.get("/api/health/ai", tags=["Health"])
@app.get("/api/backend/health/ai", tags=["Health"])
def health_ai():
    gemini_conf = gemini_provider.is_configured
    return {
        "gemini": {
            "configured": gemini_conf,
            "available": gemini_conf
        },
        "local_cv": {
            "available": True
        }
    }

# Vercel Services Swagger & Documentation Endpoints
@app.get("/api/backend/docs", include_in_schema=False)
async def backend_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/api/backend/openapi.json",
        title=f"{settings.PROJECT_TITLE} - API Docs"
    )

@app.get("/api/backend/redoc", include_in_schema=False)
async def backend_redoc_ui():
    return get_redoc_html(
        openapi_url="/api/backend/openapi.json",
        title=f"{settings.PROJECT_TITLE} - ReDoc"
    )

@app.get("/api/backend/openapi.json", include_in_schema=False)
async def backend_openapi_spec():
    return app.openapi()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
