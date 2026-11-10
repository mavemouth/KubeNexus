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
    is_demo = (cluster_data.authMethod == "demo" or 
               (cluster_data.apiEndpoint and "demo" in cluster_data.apiEndpoint.lower()))

    if is_demo:
        connection = {
            "node_count": 3,
            "version": "v1.28.2",
            "endpoint": cluster_data.apiEndpoint or "https://demo.k8s.local"
        }
    else:
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

    if is_demo:
        from app.models.schemas import Workload
        demo_wls = [
            Workload(
                id=f"{new_id}-api",
                name=f"{cluster.name.lower().replace(' ', '-')}-api",
                namespace="default",
                clusterId=cluster.id,
                clusterName=cluster.name,
                type="Deployment",
                replicasDesired=2,
                replicasAvailable=2,
                cpuRequest="1.0 Core",
                cpuLimit="2.0 Cores",
                cpuRequestCores=1.0,
                cpuLimitCores=2.0,
                cpuUsageCores=0.25,
                memoryRequestMb=1024.0,
                memoryLimitMb=2048.0,
                cpuUtilizationPct=25.0,
                memoryUtilizationPct=35.0,
                status="Healthy",
                dataQualityStatus="valid",
                restarts=0,
                oomKills=0,
                throttlingCount=0,
                lastAnalysisTime="Just now"
            ),
            Workload(
                id=f"{new_id}-worker",
                name=f"{cluster.name.lower().replace(' ', '-')}-worker",
                namespace="production",
                clusterId=cluster.id,
                clusterName=cluster.name,
                type="Deployment",
                replicasDesired=2,
                replicasAvailable=2,
                cpuRequest="2.0 Cores",
                cpuLimit="4.0 Cores",
                cpuRequestCores=2.0,
                cpuLimitCores=4.0,
                cpuUsageCores=0.45,
                memoryRequestMb=2048.0,
                memoryLimitMb=4096.0,
                cpuUtilizationPct=22.5,
                memoryUtilizationPct=25.0,
                status="Over-provisioned",
                dataQualityStatus="valid",
                restarts=0,
                oomKills=0,
                throttlingCount=0,
                lastAnalysisTime="Just now"
            )
        ]
        db.upsert_workloads(demo_wls)
        cluster.workloadCount = len(demo_wls)
        db.update_cluster(cluster)
    else:
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
