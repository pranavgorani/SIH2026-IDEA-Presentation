import os
import sys
import logging
import secrets
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic_settings import BaseSettings

logger = logging.getLogger("trustid.config")

# Determine project roots and ensure sys.path includes workspace and backend
_current_file = Path(__file__).resolve()
_core_dir = _current_file.parent
_app_dir = _core_dir.parent
_backend_dir = _app_dir.parent
_workspace_dir = _backend_dir.parent

for _p in [str(_workspace_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

BASE_DIR = _backend_dir
IS_VERCEL = bool(os.getenv("VERCEL"))
ENV = os.getenv("ENVIRONMENT", "development").lower()

def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret and secret.strip() and secret.strip() not in ("CHANGE_ME_IN_PRODUCTION", "CHANGE_ME_LOCALLY"):
        return secret.strip()
    
    # In production environments, fail clearly if secret is missing or default
    if IS_VERCEL or ENV in ("production", "prod"):
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET environment variable is missing or using default. "
            "Please generate and set a cryptographically secure key: "
            "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
        )
    
    # In local development: generate a transient cryptographically secure secret
    return secrets.token_urlsafe(48)

def get_default_db_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        # If Supabase connection URL is provided
        return os.getenv("DATABASE_URL", "sqlite:////tmp/trustid.db" if IS_VERCEL else f"sqlite:///{BASE_DIR / 'data' / 'trustid.db'}")
    if IS_VERCEL:
        return "sqlite:////tmp/trustid.db"
    # Ensure local data directory exists
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'trustid.db'}"

def get_default_storage_dir() -> Path:
    if os.getenv("STORAGE_DIR"):
        return Path(os.getenv("STORAGE_DIR"))
    if IS_VERCEL:
        return Path("/tmp/trustid_storage")
    return BASE_DIR / "storage"

def get_default_cors() -> List[str]:
    env_cors = os.getenv("CORS_ORIGINS")
    if env_cors:
        # Strictly reject wildcard in production/authenticated APIs
        origins = [o.strip() for o in env_cors.split(",") if o.strip() and o.strip() != "*"]
        if origins:
            return origins
    # Safe explicit default origins for development and local previews
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

class Settings(BaseSettings):
    PROJECT_NAME: str = "TRUST-ID"
    PROJECT_TITLE: str = "TRUST-ID — AI-Powered Identity & Document Screening Platform"
    TAGLINE: str = "Detect. Verify. Explain. Secure."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Security: Read securely from environment without hardcoded fallback credentials
    SECRET_KEY: str = get_jwt_secret()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = get_default_db_url()
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")

    # Storage
    STORAGE_DIR: Path = get_default_storage_dir()
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "trustid-documents")
    UPLOAD_MAX_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".pdf"]
    ALLOWED_MIME_TYPES: List[str] = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "application/pdf"
    ]

    # CORS (Strict origin specification; no wildcard in production)
    CORS_ORIGINS: List[str] = get_default_cors()

    # URLs
    NEXT_PUBLIC_API_URL: str = os.getenv("NEXT_PUBLIC_API_URL", "")
    BACKEND_URL: str = os.getenv("BACKEND_URL", os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000"))

    # Risk Engine Default Weights (Sum to 1.0)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "visual_forensics": 0.25,
        "identity_verification": 0.20,
        "record_verification": 0.20,
        "document_validation": 0.15,
        "ocr_consistency": 0.10,
        "mrz_validation": 0.05,
        "image_quality": 0.05
    }

    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 30.0     # 0 - 30: Low Risk
    RISK_THRESHOLD_MEDIUM: float = 60.0  # 31 - 60: Medium Risk
    # > 60: High Risk

    # System Providers (LOCAL_CV_FALLBACK or GEMINI_VISION_HYBRID)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "LOCAL_CV_FALLBACK")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # OCR & Pipeline Configuration
    OCR_ENGINE_PRIMARY: str = os.getenv("OCR_ENGINE_PRIMARY", "auto")
    OCR_MAX_PAGES: int = int(os.getenv("OCR_MAX_PAGES", "10"))
    ENABLE_PDF_PROCESSING: bool = os.getenv("ENABLE_PDF_PROCESSING", "false").lower() in ("true", "1")
    ENABLE_LOCAL_FALLBACK: bool = os.getenv("ENABLE_LOCAL_FALLBACK", "true").lower() in ("true", "1")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

def validate_environment() -> Dict[str, Any]:
    """
    Validates required and optional environment variables at startup.
    Logs warnings for missing optional services without exposing secret values.
    Returns status dictionary for health check endpoints.
    """
    env_status = {
        "database_configured": bool(settings.DATABASE_URL),
        "jwt_configured": bool(settings.SECRET_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("YOUR_GEMINI_API_KEY", "CHANGE_ME_LOCALLY")),
        "storage_configured": bool(settings.STORAGE_DIR.exists()),
        "cors_origins_count": len(settings.CORS_ORIGINS),
        "is_production": ENV in ("production", "prod") or IS_VERCEL
    }

    if not env_status["gemini_configured"]:
        logger.info("Notice: GEMINI_API_KEY is not set. System will automatically use high-performance local computer-vision fallback.")
    else:
        logger.info(f"Gemini AI provider configured with model: {settings.GEMINI_MODEL}")

    if "*" in settings.CORS_ORIGINS:
        logger.warning("SECURITY WARNING: Wildcard '*' detected in CORS_ORIGINS. Stripping for authenticated endpoint protection.")
        settings.CORS_ORIGINS = [o for o in settings.CORS_ORIGINS if o != "*"]

    return env_status
