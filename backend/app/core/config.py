import os
from pathlib import Path
from typing import List, Dict
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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

    # Database: Default to sqlite file in backend/data for zero-config local run, or PostgreSQL via env
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'trustid.db'}")

    # Storage
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_MAX_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".pdf"]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

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

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
