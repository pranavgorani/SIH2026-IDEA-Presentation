import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.models.database import init_db, SessionLocal
from backend.app.api.auth import router as auth_router, seed_demo_users_if_needed
from backend.app.api.screening import router as screening_router
from backend.app.api.cases import router as cases_router
from backend.app.api.documents import router as documents_router
from backend.app.api.audit import router as audit_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.settings import router as settings_router
from backend.app.services.synthetic_generator import synthetic_generator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    db = SessionLocal()
    try:
        seed_demo_users_if_needed(db)
    finally:
        db.close()

    # Pre-render synthetic demonstration cases so demo mode works out of the box
    try:
        synthetic_generator.generate_all_presets()
    except Exception as e:
        print(f"Notice: Synthetic document initialization: {e}")

    yield
    # Shutdown logic if needed

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

# Mount Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(screening_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ONLINE",
        "service": settings.PROJECT_NAME,
        "title": settings.PROJECT_TITLE,
        "version": settings.VERSION,
        "tagline": settings.TAGLINE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
