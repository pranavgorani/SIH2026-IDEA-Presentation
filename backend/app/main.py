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

# Mount Routers under root, /api, and /api/backend for Vercel and direct proxy compatibility
app.include_router(screening_router)
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
from backend.app.models.database import generate_uuid
from sqlalchemy import text
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("trustid.gateway")

# Global Exception Handlers
@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    req_id = generate_uuid()
    logger.exception(f"GLOBAL_UNHANDLED_EXCEPTION: request_id={req_id} path={request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "request_id": req_id,
            "stage": "GATEWAY",
            "code": "SERVICE_ERROR",
            "error_code": "SERVICE_ERROR",
            "message": "Screening service encountered an internal error. Please retry or execute with local computer-vision fallback.",
            "user_action": "Retry screening or execute with local computer-vision fallback.",
            "recoverable": True
        }
    )

# Standard Health Endpoints
@app.get("/health", tags=["Health"])
def health_root():
    # Database check
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_status = True
    except Exception:
        db_status = False

    storage_status = settings.STORAGE_DIR.exists()
    return {
        "status": "ok",
        "api": True,
        "database": db_status,
        "ocr": True,
        "ai": True,
        "storage": storage_status
    }

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
        "api": True,
        "database": db_status == "online",
        "ocr": True,
        "ai": True,
        "storage": storage_status == "online",
        "services": {
            "database": db_status,
            "ocr": "online",
            "opencv": opencv_status,
            "gemini": gemini_status,
            "storage": storage_status
        }
    }

@app.get("/health/screening", tags=["Health"])
@app.get("/api/health/screening", tags=["Health"])
@app.get("/api/backend/health/screening", tags=["Health"])
def health_screening():
    db_connected = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    ai_prov = "gemini" if gemini_provider.is_configured else "local"
    return {
        "status": "ready",
        "pipeline_stages": 10,
        "ai_provider": ai_prov,
        "ocr_engine": settings.OCR_ENGINE_PRIMARY or "auto",
        "database_connected": db_connected
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
