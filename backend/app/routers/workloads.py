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

router = APIRouter(prefix="/workloads", tags=["Workloads"])

@router.get("", response_model=List[Workload])
def get_workloads(clusterId: Optional[str] = Query(None, alias="clusterId")):
    return db.get_all_workloads(cluster_id=clusterId)

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
    return db.get_metrics(workload.id)

@router.post("/{workload_id}/analysis", response_model=AnalysisResponse)
async def run_workload_analysis(workload_id: str):
    workload = db.get_workload(workload_id)
    if not workload:
        raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")

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
