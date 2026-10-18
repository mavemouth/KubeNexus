import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

# Background periodic rule evaluator
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
    # Startup: trigger initial rule scan and spawn background task
    await alert_service.scan_and_evaluate_rules()
    task = asyncio.create_task(background_monitoring_loop())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="KubeNexus API",
    description="Kubernetes Workload Resource Optimization & Decision Support Microservice",
    version="1.4.0",
    lifespan=lifespan
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & Overview Status Endpoint
@app.get("/health", tags=["System"])
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

# Mount routers under /api/v1
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
    app.include_router(r)  # Also mount at root for seamless compatibility
