import json
import hashlib
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.orm import (
    ClusterModel,
    WorkloadModel,
    MetricSampleModel,
    RecommendationModel,
    AlertModel,
    AuditEventModel,
    EvaluationModel,
    SettingsModel
)
from app.models.schemas import (
    Cluster,
    Workload,
    Recommendation,
    AlertItem,
    AuditEvent,
    PostChangeEvaluation,
    OptimizationSettings,
    MetricTimeSeriesPoint,
    Percentiles
)

# Initialize tables upon module import
init_db()

# ====================================================================
# Mapping Helpers: SQLAlchemy ORM <-> Pydantic Schemas
# ====================================================================

def cluster_to_pydantic(m: ClusterModel) -> Cluster:
    return Cluster(
        id=m.id,
        name=m.name,
        environment=m.environment, # type: ignore
        connectionStatus=m.connection_status, # type: ignore
        lastChecked=m.last_checked,
        workloadCount=m.workload_count,
        monitoringStatus=m.monitoring_status, # type: ignore
        nodeCount=m.node_count,
        k8sVersion=m.k8s_version,
        provider=m.provider, # type: ignore
        apiEndpoint=m.api_endpoint,
        authMethod=getattr(m, "auth_method", "local") or "local",
        prometheusUrl=getattr(m, "prometheus_url", "http://localhost:9090") or "http://localhost:9090"
    )

def workload_to_pydantic(m: WorkloadModel) -> Workload:
    return Workload(
        id=m.id,
        name=m.name,
        namespace=m.namespace,
        clusterId=m.cluster_id or "",
        clusterName=m.cluster_name,
        type=m.type, # type: ignore
        replicasDesired=m.replicas_desired,
        replicasAvailable=m.replicas_available,
        cpuRequest=m.cpu_request,
        cpuLimit=m.cpu_limit,
        cpuRequestCores=m.cpu_request_cores,
        cpuLimitCores=m.cpu_limit_cores,
        cpuUsageCores=m.cpu_usage_cores,
        memoryRequestMb=m.memory_request_mb,
        memoryLimitMb=m.memory_limit_mb,
        cpuUtilizationPct=m.cpu_utilization_pct,
        memoryUtilizationPct=m.memory_utilization_pct,
        status=m.status, # type: ignore
        dataQualityStatus=m.data_quality_status, # type: ignore
        restarts=m.restarts,
        oomKills=m.oom_kills,
        throttlingCount=m.throttling_count,
        lastAnalysisTime=m.last_analysis_time
    )

def rec_to_pydantic(m: RecommendationModel) -> Recommendation:
    pct_dict = {}
    try:
        if m.percentiles_json:
            pct_dict = json.loads(m.percentiles_json)
    except Exception:
        pct_dict = {}

    percentiles = Percentiles(
        p50Cpu=pct_dict.get("p50Cpu", 0.0),
        p90Cpu=pct_dict.get("p90Cpu", 0.0),
        p99Cpu=pct_dict.get("p99Cpu", 0.0),
        maxCpu=pct_dict.get("maxCpu", 0.0),
        p50MemoryMb=pct_dict.get("p50MemoryMb", 0.0),
        p90MemoryMb=pct_dict.get("p90MemoryMb", 0.0),
        p99MemoryMb=pct_dict.get("p99MemoryMb", 0.0),
        maxMemoryMb=pct_dict.get("maxMemoryMb", 0.0)
    )

    return Recommendation(
        id=m.id,
        workloadId=m.workload_id,
        workloadName=m.workload_name,
        namespace=m.namespace,
        clusterName=m.cluster_name,
        workloadType=m.workload_type, # type: ignore
        currentCpuRequest=m.current_cpu_request,
        recommendedCpuRequest=m.recommended_cpu_request,
        currentCpuLimit=m.current_cpu_limit,
        recommendedCpuLimit=m.recommended_cpu_limit,
        currentMemoryRequest=m.current_memory_request,
        recommendedMemoryRequest=m.recommended_memory_request,
        currentMemoryLimit=m.current_memory_limit,
        recommendedMemoryLimit=m.recommended_memory_limit,
        observationWindow=m.observation_window,
        evidenceReason=m.evidence_reason,
        assumptions=m.assumptions,
        riskLevel=m.risk_level, # type: ignore
        confidence=m.confidence, # type: ignore
        estimatedMonthlySavings=m.estimated_monthly_savings,
        status=m.status, # type: ignore
        createdAt=m.created_at,
        expiresAt=m.expires_at,
        hpaDetected=m.hpa_detected,
        vpaDetected=m.vpa_detected,
        dataQualityCheckPassed=m.data_quality_check_passed,
        metricsFresh=m.metrics_fresh,
        percentiles=percentiles
    )

def alert_to_pydantic(m: AlertModel) -> AlertItem:
    return AlertItem(
        id=m.id,
        severity=m.severity, # type: ignore
        title=m.title,
        description=m.description,
        affectedWorkload=m.affected_workload,
        clusterName=m.cluster_name,
        timestamp=m.timestamp,
        status=m.status, # type: ignore
        category=m.category # type: ignore
    )

def audit_to_pydantic(m: AuditEventModel) -> AuditEvent:
    return AuditEvent(
        id=m.id,
        timestamp=m.timestamp,
        workloadName=m.workload_name,
        namespace=m.namespace,
        clusterName=m.cluster_name,
        previousCpuRequest=m.previous_cpu_request,
        newCpuRequest=m.new_cpu_request,
        previousMemoryRequest=m.previous_memory_request,
        newMemoryRequest=m.new_memory_request,
        changedBy=m.changed_by,
        userRole=m.user_role,
        action=m.action, # type: ignore
        recommendationId=m.recommendation_id,
        status=m.status # type: ignore
    )

def eval_to_pydantic(m: EvaluationModel) -> PostChangeEvaluation:
    return PostChangeEvaluation(
        id=m.id,
        workloadId=m.workload_id,
        workloadName=m.workload_name,
        namespace=m.namespace,
        clusterName=m.cluster_name,
        changeTimestamp=m.change_timestamp,
        beforeCpuRequest=m.before_cpu_request,
        afterCpuRequest=m.after_cpu_request,
        beforeMemoryRequest=m.before_memory_request,
        afterMemoryRequest=m.after_memory_request,
        beforeCpuUtilPct=m.before_cpu_util_pct,
        afterCpuUtilPct=m.after_cpu_util_pct,
        beforeMemoryUtilPct=m.before_memory_util_pct,
        afterMemoryUtilPct=m.after_memory_util_pct,
        oomKillsBefore=m.oom_kills_before,
        oomKillsAfter=m.oom_kills_after,
        restartsBefore=m.restarts_before,
        restartsAfter=m.restarts_after,
        monthlySavingsAchieved=m.monthly_savings_achieved,
        status=m.status, # type: ignore
        recommendationId=m.recommendation_id
    )

def settings_to_pydantic(m: SettingsModel) -> OptimizationSettings:
    return OptimizationSettings(
        safetyMarginPct=m.safety_margin_pct,
        minObservationDays=m.min_observation_days,
        autoApproveMinConfidence=m.auto_approve_min_confidence, # type: ignore
        prometheusUrl=m.prometheus_url,
        scrapeIntervalSeconds=m.scrape_interval_seconds,
        enableHpaSafetyCheck=m.enable_hpa_safety_check,
        enableVpaConflictCheck=m.enable_vpa_conflict_check,
        apiBaseUrl=m.api_base_url
    )

# ====================================================================
# PostgreSQL Database Service
# ====================================================================

class PostgresDatabase:
    """Production database layer connected to PostgreSQL / Supabase"""

    # Cluster queries
    def get_all_clusters(self) -> List[Cluster]:
        with SessionLocal() as session:
            rows = session.query(ClusterModel).all()
            return [cluster_to_pydantic(r) for r in rows]

    def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        with SessionLocal() as session:
            row = session.query(ClusterModel).filter(ClusterModel.id == cluster_id).first()
            return cluster_to_pydantic(row) if row else None

    def add_cluster(self, cluster: Cluster, kubeconfig_raw: Optional[str] = None, bearer_token: Optional[str] = None) -> Cluster:
        with SessionLocal() as session:
            model = ClusterModel(
                id=cluster.id,
                name=cluster.name,
                environment=cluster.environment,
                connection_status=cluster.connectionStatus,
                last_checked=cluster.lastChecked,
                workload_count=cluster.workloadCount,
                monitoring_status=cluster.monitoringStatus,
                node_count=cluster.nodeCount,
                k8s_version=cluster.k8sVersion,
                provider=cluster.provider,
                api_endpoint=cluster.apiEndpoint,
                auth_method=cluster.authMethod,
                kubeconfig_raw=kubeconfig_raw,
                bearer_token=bearer_token,
                prometheus_url=cluster.prometheusUrl
            )
            session.add(model)
            session.commit()
            return cluster

    def get_cluster_credentials(self, cluster_id: str) -> dict:
        with SessionLocal() as session:
            row = session.query(ClusterModel).filter(ClusterModel.id == cluster_id).first()
            if not row:
                return {}
            return {
                "auth_method": getattr(row, "auth_method", "local"),
                "kubeconfig_raw": getattr(row, "kubeconfig_raw", None),
                "bearer_token": getattr(row, "bearer_token", None),
                "api_endpoint": getattr(row, "api_endpoint", None),
                "prometheus_url": getattr(row, "prometheus_url", "http://localhost:9090")
            }

    # Workload queries
    def get_all_workloads(self, cluster_id: Optional[str] = None) -> List[Workload]:
        with SessionLocal() as session:
            query = session.query(WorkloadModel)
            if cluster_id:
                query = query.filter(WorkloadModel.cluster_id == cluster_id)
            rows = query.all()
            return [workload_to_pydantic(r) for r in rows]

    def get_workload(self, workload_id_or_name: str) -> Optional[Workload]:
        with SessionLocal() as session:
            row = session.query(WorkloadModel).filter(
                (WorkloadModel.id == workload_id_or_name) | (WorkloadModel.name == workload_id_or_name)
            ).first()
            return workload_to_pydantic(row) if row else None

    def add_workload(self, workload: Workload) -> Workload:
        with SessionLocal() as session:
            model = WorkloadModel(
                id=workload.id,
                name=workload.name,
                namespace=workload.namespace,
                cluster_id=workload.clusterId,
                cluster_name=workload.clusterName,
                type=workload.type,
                replicas_desired=workload.replicasDesired,
                replicas_available=workload.replicasAvailable,
                cpu_request=workload.cpuRequest,
                cpu_limit=workload.cpuLimit,
                cpu_request_cores=workload.cpuRequestCores,
                cpu_limit_cores=workload.cpuLimitCores,
                cpu_usage_cores=workload.cpuUsageCores,
                memory_request_mb=workload.memoryRequestMb,
                memory_limit_mb=workload.memoryLimitMb,
                cpu_utilization_pct=workload.cpuUtilizationPct,
                memory_utilization_pct=workload.memoryUtilizationPct,
                status=workload.status,
                data_quality_status=workload.dataQualityStatus,
                restarts=workload.restarts,
                oom_kills=workload.oomKills,
                throttling_count=workload.throttlingCount,
                last_analysis_time=workload.lastAnalysisTime
            )
            session.add(model)
            session.commit()
            return workload

    def upsert_workloads(self, workloads: List[Workload]) -> None:
        """Persist the latest discovered Kubernetes workload configuration."""
        with SessionLocal() as session:
            for workload in workloads:
                model = session.query(WorkloadModel).filter(WorkloadModel.id == workload.id).first()
                if model is None:
                    model = WorkloadModel(id=workload.id, name=workload.name, namespace=workload.namespace,
                                          cluster_name=workload.clusterName)
                    session.add(model)
                else:
                    # Return the last collected evidence with newly discovered
                    # Kubernetes configuration in the same API response.
                    workload.cpuUsageCores = model.cpu_usage_cores or 0.0
                    workload.cpuUtilizationPct = model.cpu_utilization_pct or 0.0
                    workload.memoryUtilizationPct = model.memory_utilization_pct or 0.0
                    workload.dataQualityStatus = model.data_quality_status or workload.dataQualityStatus
                    workload.lastAnalysisTime = model.last_analysis_time or workload.lastAnalysisTime
                model.name = workload.name
                model.namespace = workload.namespace
                model.cluster_id = workload.clusterId
                model.cluster_name = workload.clusterName
                model.type = workload.type
                model.replicas_desired = workload.replicasDesired
                model.replicas_available = workload.replicasAvailable
                model.cpu_request = workload.cpuRequest
                model.cpu_limit = workload.cpuLimit
                model.cpu_request_cores = workload.cpuRequestCores
                model.cpu_limit_cores = workload.cpuLimitCores
                # Preserve utilization previously collected from Prometheus.
                model.memory_request_mb = workload.memoryRequestMb
                model.memory_limit_mb = workload.memoryLimitMb
                # Preserve utilization percentages across inventory refreshes.
                model.status = workload.status
                # Preserve the current evidence status across inventory refreshes.
                model.restarts = workload.restarts
                model.oom_kills = workload.oomKills
                # Preserve metrics collection metadata across inventory refreshes.
            session.commit()

    def update_workload(self, workload: Workload) -> Workload:
        with SessionLocal() as session:
            row = session.query(WorkloadModel).filter(WorkloadModel.id == workload.id).first()
            if row:
                row.name = workload.name
                row.namespace = workload.namespace
                row.cluster_id = workload.clusterId
                row.cluster_name = workload.clusterName
                row.type = workload.type
                row.replicas_desired = workload.replicasDesired
                row.replicas_available = workload.replicasAvailable
                row.cpu_request = workload.cpuRequest
                row.cpu_limit = workload.cpuLimit
                row.cpu_request_cores = workload.cpuRequestCores
                row.cpu_limit_cores = workload.cpuLimitCores
                row.cpu_usage_cores = workload.cpuUsageCores
                row.memory_request_mb = workload.memoryRequestMb
                row.memory_limit_mb = workload.memoryLimitMb
                row.cpu_utilization_pct = workload.cpuUtilizationPct
                row.memory_utilization_pct = workload.memoryUtilizationPct
                row.status = workload.status
                row.data_quality_status = workload.dataQualityStatus
                row.restarts = workload.restarts
                row.oom_kills = workload.oomKills
                row.throttling_count = workload.throttlingCount
                row.last_analysis_time = workload.lastAnalysisTime
                session.commit()
            else:
                self.add_workload(workload)
            return workload

    # Recommendation queries
    def get_all_recommendations(self) -> List[Recommendation]:
        with SessionLocal() as session:
            rows = session.query(RecommendationModel).all()
            return [rec_to_pydantic(r) for r in rows]

    def get_recommendation(self, rec_id: str) -> Optional[Recommendation]:
        with SessionLocal() as session:
            row = session.query(RecommendationModel).filter(RecommendationModel.id == rec_id).first()
            return rec_to_pydantic(row) if row else None

    def save_recommendation(self, rec: Recommendation) -> Recommendation:
        with SessionLocal() as session:
            row = session.query(RecommendationModel).filter(RecommendationModel.id == rec.id).first()
            pct_json = json.dumps(rec.percentiles.model_dump())
            if row:
                row.status = rec.status
                row.current_cpu_request = rec.currentCpuRequest
                row.recommended_cpu_request = rec.recommendedCpuRequest
                row.current_cpu_limit = rec.currentCpuLimit
                row.recommended_cpu_limit = rec.recommendedCpuLimit
                row.current_memory_request = rec.currentMemoryRequest
                row.recommended_memory_request = rec.recommendedMemoryRequest
                row.current_memory_limit = rec.currentMemoryLimit
                row.recommended_memory_limit = rec.recommendedMemoryLimit
                row.evidence_reason = rec.evidenceReason
                row.estimated_monthly_savings = rec.estimatedMonthlySavings
                row.percentiles_json = pct_json
                session.commit()
            else:
                model = RecommendationModel(
                    id=rec.id,
                    workload_id=rec.workloadId,
                    workload_name=rec.workloadName,
                    namespace=rec.namespace,
                    cluster_name=rec.clusterName,
                    workload_type=rec.workloadType,
                    current_cpu_request=rec.currentCpuRequest,
                    recommended_cpu_request=rec.recommendedCpuRequest,
                    current_cpu_limit=rec.currentCpuLimit,
                    recommended_cpu_limit=rec.recommendedCpuLimit,
                    current_memory_request=rec.currentMemoryRequest,
                    recommended_memory_request=rec.recommendedMemoryRequest,
                    current_memory_limit=rec.currentMemoryLimit,
                    recommended_memory_limit=rec.recommendedMemoryLimit,
                    observation_window=rec.observationWindow,
                    evidence_reason=rec.evidenceReason,
                    assumptions=rec.assumptions,
                    risk_level=rec.riskLevel,
                    confidence=rec.confidence,
                    estimated_monthly_savings=rec.estimatedMonthlySavings,
                    status=rec.status,
                    created_at=rec.createdAt,
                    expires_at=rec.expiresAt,
                    hpa_detected=rec.hpaDetected,
                    vpa_detected=rec.vpaDetected,
                    data_quality_check_passed=rec.dataQualityCheckPassed,
                    metrics_fresh=rec.metricsFresh,
                    percentiles_json=pct_json
                )
                session.add(model)
                session.commit()
            return rec

    # Alert queries
    def get_all_alerts(self) -> List[AlertItem]:
        with SessionLocal() as session:
            rows = session.query(AlertModel).all()
            sev_order = {"Critical": 0, "Warning": 1, "Info": 2}
            alerts = [alert_to_pydantic(r) for r in rows]
            return sorted(alerts, key=lambda a: sev_order.get(a.severity, 3))

    def get_alert(self, alert_id: str) -> Optional[AlertItem]:
        with SessionLocal() as session:
            row = session.query(AlertModel).filter(AlertModel.id == alert_id).first()
            return alert_to_pydantic(row) if row else None

    def save_alert(self, alert: AlertItem) -> AlertItem:
        with SessionLocal() as session:
            row = session.query(AlertModel).filter(AlertModel.id == alert.id).first()
            if row:
                row.status = alert.status
                session.commit()
            else:
                model = AlertModel(
                    id=alert.id,
                    severity=alert.severity,
                    title=alert.title,
                    description=alert.description,
                    affected_workload=alert.affectedWorkload,
                    cluster_name=alert.clusterName,
                    timestamp=alert.timestamp,
                    status=alert.status,
                    category=alert.category
                )
                session.add(model)
                session.commit()
            return alert

    # Audit queries
    def get_all_audit_events(self) -> List[AuditEvent]:
        with SessionLocal() as session:
            rows = session.query(AuditEventModel).order_by(AuditEventModel.created_at.desc()).all()
            return [audit_to_pydantic(r) for r in rows]

    def add_audit_event(self, event: AuditEvent):
        with SessionLocal() as session:
            model = AuditEventModel(
                id=event.id,
                timestamp=event.timestamp,
                workload_name=event.workloadName,
                namespace=event.namespace,
                cluster_name=event.clusterName,
                previous_cpu_request=event.previousCpuRequest,
                new_cpu_request=event.newCpuRequest,
                previous_memory_request=event.previousMemoryRequest,
                new_memory_request=event.newMemoryRequest,
                changed_by=event.changedBy,
                user_role=event.userRole,
                action=event.action,
                recommendation_id=event.recommendationId,
                status=event.status
            )
            session.add(model)
            session.commit()

    # Evaluation queries
    def get_all_evaluations(self) -> List[PostChangeEvaluation]:
        with SessionLocal() as session:
            rows = session.query(EvaluationModel).order_by(EvaluationModel.created_at.desc()).all()
            return [eval_to_pydantic(r) for r in rows]

    def add_evaluation(self, eval_item: PostChangeEvaluation):
        with SessionLocal() as session:
            model = EvaluationModel(
                id=eval_item.id,
                workload_id=eval_item.workloadId,
                workload_name=eval_item.workloadName,
                namespace=eval_item.namespace,
                cluster_name=eval_item.clusterName,
                change_timestamp=eval_item.changeTimestamp,
                before_cpu_request=eval_item.beforeCpuRequest,
                after_cpu_request=eval_item.afterCpuRequest,
                before_memory_request=eval_item.beforeMemoryRequest,
                after_memory_request=eval_item.afterMemoryRequest,
                before_cpu_util_pct=eval_item.beforeCpuUtilPct,
                after_cpu_util_pct=eval_item.afterCpuUtilPct,
                before_memory_util_pct=eval_item.beforeMemoryUtilPct,
                after_memory_util_pct=eval_item.afterMemoryUtilPct,
                oom_kills_before=eval_item.oomKillsBefore,
                oom_kills_after=eval_item.oomKillsAfter,
                restarts_before=eval_item.restartsBefore,
                restarts_after=eval_item.restartsAfter,
                monthly_savings_achieved=eval_item.monthlySavingsAchieved,
                status=eval_item.status,
                recommendation_id=eval_item.recommendationId
            )
            session.add(model)
            session.commit()

    # Metrics queries
    def get_metrics(self, workload_id_or_name: str) -> List[MetricTimeSeriesPoint]:
        workload = self.get_workload(workload_id_or_name)
        if not workload:
            return []
        with SessionLocal() as session:
            rows = (session.query(MetricSampleModel)
                    .filter(MetricSampleModel.workload_id == workload.id)
                    .order_by(MetricSampleModel.timestamp.asc()).all())
            return [MetricTimeSeriesPoint(
                timestamp=row.timestamp, cpuUsage=row.cpu_usage,
                cpuRequest=row.cpu_request, cpuLimit=row.cpu_limit,
                memoryUsageMb=row.memory_usage_mb, memoryLimitMb=row.memory_limit_mb
            ) for row in rows]

    def store_metrics(self, workload_id: str, points: List[MetricTimeSeriesPoint]) -> None:
        with SessionLocal() as session:
            for point in points:
                sample_key = f"{workload_id}:{point.timestamp}".encode("utf-8")
                sample_id = hashlib.sha256(sample_key).hexdigest()
                if session.query(MetricSampleModel.id).filter(MetricSampleModel.id == sample_id).first():
                    continue
                session.add(MetricSampleModel(
                    id=sample_id, workload_id=workload_id, timestamp=point.timestamp,
                    cpu_usage=point.cpuUsage, cpu_request=point.cpuRequest,
                    cpu_limit=point.cpuLimit, memory_usage_mb=point.memoryUsageMb,
                    memory_limit_mb=point.memoryLimitMb,
                ))
            session.commit()

    # Settings queries
    def get_settings(self) -> OptimizationSettings:
        with SessionLocal() as session:
            row = session.query(SettingsModel).first()
            if row:
                return settings_to_pydantic(row)
            # Default settings if table empty
            return OptimizationSettings()

    def update_settings(self, new_settings: OptimizationSettings) -> OptimizationSettings:
        with SessionLocal() as session:
            row = session.query(SettingsModel).first()
            if not row:
                row = SettingsModel(id=1)
                session.add(row)
            row.safety_margin_pct = new_settings.safetyMarginPct
            row.min_observation_days = new_settings.minObservationDays
            row.auto_approve_min_confidence = new_settings.autoApproveMinConfidence
            row.prometheus_url = new_settings.prometheusUrl
            row.scrape_interval_seconds = new_settings.scrapeIntervalSeconds
            row.enable_hpa_safety_check = new_settings.enableHpaSafetyCheck
            row.enable_vpa_conflict_check = new_settings.enableVpaConflictCheck
            row.api_base_url = new_settings.apiBaseUrl
            session.commit()
            return new_settings

# Global database instance
db = PostgresDatabase()
