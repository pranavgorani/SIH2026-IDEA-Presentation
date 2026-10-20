# ==============================================================================
# TRUST-ID — Authoritative Backend Entrypoint
# Supports:
# 1. Monorepo root execution: `uvicorn backend.app.main:app` or `uvicorn backend.main:app`
# 2. Backend root execution: `uvicorn app.main:app` or `uvicorn main:app`
# 3. Docker execution: `uvicorn backend.app.main:app`
# ==============================================================================
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent
_workspace_dir = _backend_dir.parent

for _p in [str(_workspace_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.app.main import app  # noqa: F401
