import os
import re
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    clusters,
    workloads,
    recommendations,
    alerts,
    audit,
    evaluation,
    cost,
    settings
)
from app.services.alert_service import alert_service
from app.storage.db import db

# Background periodic rule evaluator (skipped in serverless runtime)
async def background_monitoring_loop():
    while True:
        try:
            await asyncio.sleep(60)
            await alert_service.scan_and_evaluate_rules()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Warning] Error in background monitoring loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: trigger initial rule scan
    try:
        await alert_service.scan_and_evaluate_rules()
    except Exception as e:
        print(f"[Warning] Rule evaluation on startup skipped: {e}")
    
    # In serverless environments (like Vercel), long-running infinite loops are skipped
    task = None
    if not os.getenv("VERCEL"):
        task = asyncio.create_task(background_monitoring_loop())
    yield
    # Shutdown
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="KubeNexus API",
    description="Kubernetes Workload Resource Optimization & Decision Support Microservice",
    version="1.4.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# ── Dynamic CORS Configuration ───────────────────────────────────────
# Default allowed origins: production frontend + local development
default_origins = [
    "https://kube-nexus-navy.vercel.app",
    "https://kube-nexus-1z5e.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

# Read optional extra origins from environment variable (comma-separated)
env_origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
allowed_origins = list(default_origins)
if env_origins_raw:
    for origin in env_origins_raw.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

# Regex matching any Vercel deployment URL (production, preview, staging) + localhost
origin_regex = r"^https:\/\/.*\.vercel\.app$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Global exception handler to guarantee proper CORS headers on 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    origin = request.headers.get("origin", "")
    cors_origin = origin if (origin and (origin in allowed_origins or re.match(origin_regex, origin))) else (allowed_origins[0] if allowed_origins else "*")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        }
    )

# Root Platform Discovery Endpoint
@app.get("/", tags=["System"])
@app.get("/api", tags=["System"])
@app.get("/api/index.py", tags=["System"])
def root_status():
    return {
        "service": "KubeNexus API",
        "status": "online",
        "version": "1.4.0",
        "docs": "/docs",
        "health": "/health",
        "apiPrefix": "/api/v1"
    }

# Health & Overview Status Endpoint
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
@app.get("/v1/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "kubenexus-backend",
        "version": "1.4.0",
        "clustersCount": len(db.get_all_clusters()),
        "workloadsCount": len(db.get_all_workloads()),
        "activeRecommendations": len([r for r in db.get_all_recommendations() if r.status in ["Generated", "Approved"]]),
        "activeAlerts": len([a for a in db.get_all_alerts() if a.status == "Active"])
    }

# Mount routers under /api/v1, /v1, /api, and root
api_v1_routers = [
    clusters.router,
    workloads.router,
    recommendations.router,
    alerts.router,
    audit.router,
    evaluation.router,
    cost.router,
    settings.router
]

for r in api_v1_routers:
    app.include_router(r, prefix="/api/v1")
    app.include_router(r, prefix="/v1")
    app.include_router(r, prefix="/api")
    app.include_router(r)  # Mount at root for seamless compatibility
