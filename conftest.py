import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"

for p in [str(root_dir), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("AI_PROVIDER", "LOCAL_CV_FALLBACK")
