from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.schemas import (
    Workload,
    MetricTimeSeriesPoint,
    Recommendation,
    AnalysisResponse
)
from app.storage.db import db
from app.services.recommendation_service import recommendation_service
from app.services.cluster_collector import cluster_collector

router = APIRouter(prefix="/workloads", tags=["Workloads"])

@router.get("", response_model=List[Workload])
def get_workloads(clusterId: Optional[str] = Query(None, alias="clusterId")):
    clusters = [db.get_cluster(clusterId)] if clusterId else db.get_all_clusters()
    clusters = [cluster for cluster in clusters if cluster]
    if not clusters:
        return []
    result = []
    for cluster in clusters:
        try:
            result.extend(cluster_collector.discover(cluster))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    db.upsert_workloads(result)
    return result

@router.post("", response_model=Workload)
def create_workload(workload: Workload):
    return db.add_workload(workload)

@router.get("/{workload_id}", response_model=Workload)
def get_workload(workload_id: str):
    workload = db.get_workload(workload_id)
    if not workload:
        raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")
    return workload

@router.get("/{workload_id}/configuration")
def get_workload_configuration(workload_id: str):
    workload = db.get_workload(workload_id)
    if not workload:
        raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")
    return {
        "id": workload.id,
        "name": workload.name,
        "namespace": workload.namespace,
        "clusterName": workload.clusterName,
        "type": workload.type,
        "cpuRequest": workload.cpuRequest,
        "cpuLimit": workload.cpuLimit,
        "memoryRequestMb": workload.memoryRequestMb,
        "memoryLimitMb": workload.memoryLimitMb,
        "replicasDesired": workload.replicasDesired,
        "replicasAvailable": workload.replicasAvailable
    }

@router.get("/{workload_id}/metrics", response_model=List[MetricTimeSeriesPoint])
def get_workload_metrics(workload_id: str, range: Optional[str] = Query("24h")):
    workload = db.get_workload(workload_id)
    if not workload:
        raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")
    cluster = db.get_cluster(workload.clusterId)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster for workload was not found")
    try:
        points = cluster_collector.metrics(cluster, workload, range or "24h")
        db.store_metrics(workload.id, points)
        # Keep the inventory and recommendation gate in sync with the live
        # Prometheus series. Discovery refreshes Kubernetes configuration, but
        # this endpoint is the point at which utilization evidence is available.
        ordered = sorted(points, key=lambda point: point.timestamp)
        cpu_values = [point.cpuUsage for point in ordered]
        memory_values = [point.memoryUsageMb for point in ordered]
        workload.cpuUsageCores = sum(cpu_values) / len(cpu_values)
        workload.cpuUtilizationPct = (
            workload.cpuUsageCores / (workload.cpuRequestCores * workload.replicasDesired) * 100
            if workload.cpuRequestCores > 0 and workload.replicasDesired > 0 else 0.0
        )
        avg_memory = sum(memory_values) / len(memory_values)
        workload.memoryUtilizationPct = (
            avg_memory / (workload.memoryRequestMb * workload.replicasDesired) * 100
            if workload.memoryRequestMb > 0 and workload.replicasDesired > 0 else 0.0
        )
        from datetime import datetime
        try:
            first = datetime.fromisoformat(ordered[0].timestamp.replace("Z", "+00:00"))
            last = datetime.fromisoformat(ordered[-1].timestamp.replace("Z", "+00:00"))
            observed_days = max(0.0, (last - first).total_seconds() / 86400)
        except (ValueError, IndexError):
            observed_days = 0.0
        minimum_days = db.get_settings().minObservationDays
        enough_samples = len(ordered) >= 2 and observed_days >= minimum_days
        workload.dataQualityStatus = "valid" if enough_samples else "insufficient_evidence"
        workload.lastAnalysisTime = f"Collected {len(ordered)} Prometheus samples"
        db.update_workload(workload)
        return points
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.post("/{workload_id}/analysis", response_model=AnalysisResponse)
async def run_workload_analysis(workload_id: str):
    workload = db.get_workload(workload_id)
    if not workload:
        raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")

    if workload.dataQualityStatus != "valid":
        raise HTTPException(
            status_code=409,
            detail="Recommendation analysis is disabled until historical Prometheus metrics are collected and validated."
        )

    rec = await recommendation_service.analyze_workload(workload.id)
    
    return AnalysisResponse(
        status="success",
        message="Optimization telemetry analysis completed successfully.",
        workloadId=workload.id,
        recommendation=rec,
        provisioningStatus=workload.status,
        utilizationDetails={
            "cpuUtilizationPct": workload.cpuUtilizationPct,
            "memoryUtilizationPct": workload.memoryUtilizationPct,
            "throttlingCount": workload.throttlingCount,
            "oomKills": workload.oomKills
        }
    )
