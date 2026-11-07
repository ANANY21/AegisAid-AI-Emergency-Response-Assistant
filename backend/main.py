"""
AegisAid - AI Emergency Response Assistant
Production Railway & ASGI Entrypoint
===========================================
This module serves as the primary ASGI entrypoint for Railway and Docker deployments.
It allows running:
    uvicorn main:app --host 0.0.0.0 --port $PORT
as well as:
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
and direct script execution:
    python main.py
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Environment & Path Normalization for Railway
# ---------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Ensure parent directory is also accessible if running from repository root
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.append(str(PARENT_DIR))

# ---------------------------------------------------------------------------
# 2. Transparent Module Aliasing
# ---------------------------------------------------------------------------
# When Railway sets Root Directory: backend, sys.path starts at 'backend/'.
# If legacy code or tests import `backend.app...` or `from backend.nlp...`,
# map 'backend' in sys.modules to the current directory structure.
try:
    import app
    if "backend" not in sys.modules:
        sys.modules["backend"] = sys.modules[__name__]
    if "backend.app" not in sys.modules:
        sys.modules["backend.app"] = app
except Exception as e:
    pass

# ---------------------------------------------------------------------------
# 3. Export ASGI FastAPI Application
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402

__all__ = ["app"]

# ---------------------------------------------------------------------------
# 4. Direct Execution Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", os.environ.get("PORT", 8000)))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting AegisAid Production Server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
