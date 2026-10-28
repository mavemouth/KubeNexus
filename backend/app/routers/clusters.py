from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from app.models.schemas import Cluster, ClusterCreate, Workload
from app.storage.db import db
from app.services.cluster_collector import cluster_collector

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

@router.post("", response_model=Cluster)
def create_cluster(cluster_data: ClusterCreate):
    try:
        connection = cluster_collector.verify(
            requested_endpoint=cluster_data.apiEndpoint,
            auth_method=cluster_data.authMethod or "local",
            kubeconfig_raw=cluster_data.kubeconfigRaw,
            bearer_token=cluster_data.bearerToken
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    new_id = f"cluster-{uuid4().hex[:12]}"
    cluster = Cluster(
        id=new_id,
        name=cluster_data.name,
        environment=cluster_data.environment or "production",
        connectionStatus="Connected",
        lastChecked="Just now",
        workloadCount=0,
        monitoringStatus="Healthy",
        nodeCount=connection["node_count"],
        k8sVersion=connection["version"],
        provider=cluster_data.provider or "AWS EKS",
        apiEndpoint=connection["endpoint"],
        authMethod=cluster_data.authMethod or "local",
        prometheusUrl=cluster_data.prometheusUrl or "http://localhost:9090"
    )
    db.add_cluster(
        cluster,
        kubeconfig_raw=cluster_data.kubeconfigRaw,
        bearer_token=cluster_data.bearerToken
    )
    try:
        workloads = cluster_collector.discover(cluster)
        cluster.workloadCount = len(workloads)
        db.upsert_workloads(workloads)
    except Exception:
        pass
    return cluster

@router.get("/{cluster_id}/workloads", response_model=List[Workload])
def get_cluster_workloads(cluster_id: str):
    cluster = db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")
    try:
        workloads = cluster_collector.discover(cluster)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    db.upsert_workloads(workloads)
    return workloads
