from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.schemas import Cluster, ClusterCreate, Workload
from app.storage.db import db

router = APIRouter(prefix="/clusters", tags=["Clusters"])

@router.get("", response_model=List[Cluster])
def get_clusters():
    return db.get_all_clusters()

@router.get("/{cluster_id}", response_model=Cluster)
def get_cluster(cluster_id: str):
    cluster = db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")
    return cluster

from datetime import datetime, timezone

@router.post("", response_model=Cluster)
def create_cluster(cluster_data: ClusterCreate):
    new_id = f"cluster-{int(datetime.now(timezone.utc).timestamp())}"
    cluster = Cluster(
        id=new_id,
        name=cluster_data.name,
        environment=cluster_data.environment or "production",
        connectionStatus="Connected",
        lastChecked="Just now",
        workloadCount=0,
        monitoringStatus="Healthy",
        nodeCount=cluster_data.nodeCount or 3,
        k8sVersion="v1.28.2",
        provider=cluster_data.provider or "AWS EKS",
        apiEndpoint=cluster_data.apiEndpoint or "https://api.k8s.local"
    )
    db.add_cluster(cluster)
    return cluster

@router.get("/{cluster_id}/workloads", response_model=List[Workload])
def get_cluster_workloads(cluster_id: str):
    cluster = db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")
    return db.get_all_workloads(cluster_id=cluster_id)
