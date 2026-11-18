# pyright: reportMissingImports=false
import os
import sys
import re
import urllib.parse
from pathlib import Path

# Ensure backend root directory is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app as fastapi_app

class VercelPathFixASGI:
    """
    ASGI middleware for Vercel Serverless Functions.
    Restores the client's actual requested path from the __path__ query param or headers,
    stripping Vercel entrypoint artifacts so FastAPI routes match cleanly.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            query_bytes = scope.get("query_string", b"")
            query_str = query_bytes.decode("utf-8", errors="ignore")
            
            real_path = ""
            new_query = query_bytes

            if "__path__=" in query_str:
                parsed = urllib.parse.parse_qs(query_str, keep_blank_values=True)
                if "__path__" in parsed:
                    real_path = parsed.pop("__path__", [""])[0]
                    new_query = urllib.parse.urlencode([(k, v) for k, vs in parsed.items() for v in vs]).encode("utf-8")

            if not real_path:
                headers = dict(scope.get("headers", []))
                real_path = (
                    headers.get(b"x-matched-path", b"").decode("utf-8", errors="ignore")
                    or headers.get(b"x-forwarded-uri", b"").decode("utf-8", errors="ignore")
                    or headers.get(b"x-original-url", b"").decode("utf-8", errors="ignore")
                )

            curr = scope.get("path", "")
            if real_path and real_path not in ("/api/index.py", "/api/index", "/api"):
                if not real_path.startswith("/"):
                    real_path = "/" + real_path
                real_path = re.sub(r"/+", "/", real_path)
                scope["path"] = real_path
                scope["raw_path"] = real_path.encode("utf-8")
                scope["query_string"] = new_query
            elif curr.startswith("/api/index.py"):
                cleaned = curr.replace("/api/index.py", "", 1) or "/"
                cleaned = re.sub(r"/+", "/", cleaned)
                scope["path"] = cleaned
                scope["raw_path"] = cleaned.encode("utf-8")
            elif curr.startswith("/api/index"):
                cleaned = curr.replace("/api/index", "", 1) or "/"
                cleaned = re.sub(r"/+", "/", cleaned)
                scope["path"] = cleaned
                scope["raw_path"] = cleaned.encode("utf-8")

        await self.app(scope, receive, send)

app = VercelPathFixASGI(fastapi_app)
handler = app
