# pyright: reportMissingImports=false
import os
import sys
from pathlib import Path

# Ensure backend root directory is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app as fastapi_app

class VercelPathFixASGI:
    """
    ASGI middleware for Vercel Serverless Functions.
    When Vercel rewrites requests to /api/index.py, scope['path'] is often
    set to '/api/index.py' instead of the client's original requested URL.
    This middleware restores the original URL from Vercel's x-matched-path,
    x-forwarded-uri, or strips function prefix artifacts so FastAPI routes match.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            # Vercel sends the client request path in x-matched-path
            real_path = (
                headers.get(b"x-matched-path", b"").decode("utf-8")
                or headers.get(b"x-forwarded-uri", b"").decode("utf-8")
                or headers.get(b"x-original-url", b"").decode("utf-8")
            )
            curr = scope.get("path", "")
            
            if real_path and (curr in ("/api/index.py", "/api/index", "/api", "") or curr.startswith("/api/index.py")):
                scope["path"] = real_path
                scope["raw_path"] = real_path.encode("utf-8")
            elif curr.startswith("/api/index.py"):
                cleaned = curr.replace("/api/index.py", "", 1) or "/"
                scope["path"] = cleaned
                scope["raw_path"] = cleaned.encode("utf-8")
            elif curr.startswith("/api/index"):
                cleaned = curr.replace("/api/index", "", 1) or "/"
                scope["path"] = cleaned
                scope["raw_path"] = cleaned.encode("utf-8")

        await self.app(scope, receive, send)

app = VercelPathFixASGI(fastapi_app)
handler = app
