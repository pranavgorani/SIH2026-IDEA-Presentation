import os
import sys
from pathlib import Path
from typing import List, Dict
from pydantic_settings import BaseSettings

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

def get_default_db_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
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
        return [o.strip() for o in env_cors.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

class Settings(BaseSettings):
    PROJECT_NAME: str = "TRUST-ID"
    PROJECT_TITLE: str = "TRUST-ID — AI-Powered Identity & Document Screening Platform"
    TAGLINE: str = "Detect. Verify. Explain. Secure."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET", "trustid-secure-sih2026-production-token-secret-key-mha")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = get_default_db_url()

    # Storage
    STORAGE_DIR: Path = get_default_storage_dir()
    UPLOAD_MAX_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".pdf"]

    # CORS
    CORS_ORIGINS: List[str] = get_default_cors()

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

    # System Providers
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "LocalModelProvider")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
