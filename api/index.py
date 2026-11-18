# pyright: reportMissingImports=false
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app.*' imports resolve cleanly
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

for p in (str(backend_dir), str(root_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Ensure VERCEL environment flag is detected
os.environ["VERCEL"] = "1"

try:
    from app.main import app  # type: ignore
except ImportError:
    from backend.app.main import app  # type: ignore

# Expose both app and handler for Vercel's ASGI runtime
handler = app
