import sys
from pathlib import Path

tests_dir = Path(__file__).resolve().parent
backend_dir = tests_dir.parent
root_dir = backend_dir.parent

for p in [str(root_dir), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("AI_PROVIDER", "LOCAL_CV_FALLBACK")

try:
    from backend.app.core.config import settings
    settings.AI_PROVIDER = "LOCAL_CV_FALLBACK"
except Exception:
    pass
