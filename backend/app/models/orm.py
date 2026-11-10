from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.sql import func
from app.database import Base

class ClusterModel(Base):
    __tablename__ = "clusters"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    environment = Column(String(32), default="production")
    connection_status = Column(String(32), default="Connected")
    last_checked = Column(String(64), default="Just now")
    workload_count = Column(Integer, default=0)
    monitoring_status = Column(String(32), default="Healthy")
    node_count = Column(Integer, default=3)
    k8s_version = Column(String(32), default="v1.28.2")
    provider = Column(String(64), default="AWS EKS")
    api_endpoint = Column(String(255), default="https://api.k8s.local")
    auth_method = Column(String(32), default="local")
    kubeconfig_raw = Column(Text, nullable=True)
    bearer_token = Column(Text, nullable=True)
    prometheus_url = Column(String(255), default="http://localhost:9090")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkloadModel(Base):
    __tablename__ = "workloads"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    namespace = Column(String(64), nullable=False, index=True)
    cluster_id = Column(String(64), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    cluster_name = Column(String(128), nullable=False)
    type = Column(String(32), default="Deployment")
    replicas_desired = Column(Integer, default=1)
    replicas_available = Column(Integer, default=1)
    cpu_request = Column(String(32), default="1.0 Core")
    cpu_limit = Column(String(32), default="2.0 Cores")
    cpu_request_cores = Column(Float, default=1.0)
    cpu_limit_cores = Column(Float, default=2.0)
    cpu_usage_cores = Column(Float, default=0.5)
    memory_request_mb = Column(Float, default=1024.0)
    memory_limit_mb = Column(Float, default=2048.0)
    cpu_utilization_pct = Column(Float, default=50.0)
    memory_utilization_pct = Column(Float, default=50.0)
    status = Column(String(32), default="Healthy")
    data_quality_status = Column(String(32), default="valid")
    restarts = Column(Integer, default=0)
    oom_kills = Column(Integer, default=0)
    throttling_count = Column(Integer, default=0)
    last_analysis_time = Column(String(64), default="Just now")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MetricSampleModel(Base):
    __tablename__ = "metric_samples"

    id = Column(String(64), primary_key=True, index=True)
    workload_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(64), nullable=False, index=True)
    cpu_usage = Column(Float, nullable=False)
    cpu_request = Column(Float, nullable=False)
    cpu_limit = Column(Float, nullable=False)
    memory_usage_mb = Column(Float, nullable=False)
    memory_limit_mb = Column(Float, nullable=False)

class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    workload_id = Column(String(64), nullable=False, index=True)
    workload_name = Column(String(128), nullable=False)
    namespace = Column(String(64), nullable=False)
    cluster_name = Column(String(128), nullable=False)
    workload_type = Column(String(32), default="Deployment")

    current_cpu_request = Column(String(32), default="1.0 Core")
    recommended_cpu_request = Column(String(32), default="1.0 Core")
    current_cpu_limit = Column(String(32), default="2.0 Cores")
    recommended_cpu_limit = Column(String(32), default="2.0 Cores")

    current_memory_request = Column(String(32), default="1.0 GB")
    recommended_memory_request = Column(String(32), default="1.0 GB")
    current_memory_limit = Column(String(32), default="2.0 GB")
    recommended_memory_limit = Column(String(32), default="2.0 GB")

    observation_window = Column(String(64), default="7-day continuous analysis")
    evidence_reason = Column(Text, default="")
    assumptions = Column(Text, default="")
    risk_level = Column(String(16), default="Low")
    confidence = Column(String(16), default="High")
    estimated_monthly_savings = Column(Float, default=0.0)
    status = Column(String(32), default="Generated") # Generated, Approved, Applied, Rejected, Expired
    created_at = Column(String(64), default="Just now")
    expires_at = Column(String(64), default="In 7 days")

    hpa_detected = Column(Boolean, default=False)
    vpa_detected = Column(Boolean, default=False)
    data_quality_check_passed = Column(Boolean, default=True)
    metrics_fresh = Column(Boolean, default=True)

    # Phase 2: Autoscaler and Safety metadata
    autoscaler_status = Column(String(64), default="NOT_CONFIGURED")
    safety_status = Column(String(32), default="SAFE")
    safety_warnings_json = Column(Text, default="[]")
    blocked_reasons_json = Column(Text, default="[]")
    requires_manual_review = Column(Boolean, default=False)

    percentiles_json = Column(Text, default="{}")

class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, index=True)
    severity = Column(String(16), default="Info") # Critical, Warning, Info
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    affected_workload = Column(String(128), default="")
    cluster_name = Column(String(128), default="")
    timestamp = Column(String(64), default="Just now")
    status = Column(String(32), default="Active") # Active, Acknowledged, Resolved
    category = Column(String(32), default="Utilization")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(String(64), default="Just now")
    workload_name = Column(String(128), nullable=False)
    namespace = Column(String(64), default="production")
    cluster_name = Column(String(128), default="primary-eks-cluster")
    previous_cpu_request = Column(String(32), default="")
    new_cpu_request = Column(String(32), default="")
    previous_memory_request = Column(String(32), default="")
    new_memory_request = Column(String(32), default="")
    changed_by = Column(String(128), default="Alex M.")
    user_role = Column(String(128), default="DevOps Engineer")
    action = Column(String(32), default="Approved")
    recommendation_id = Column(String(64), default="")
    status = Column(String(32), default="Completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EvaluationModel(Base):
    __tablename__ = "evaluations"

    id = Column(String(64), primary_key=True, index=True)
    workload_id = Column(String(64), nullable=False, index=True)
    workload_name = Column(String(128), nullable=False)
    namespace = Column(String(64), default="production")
    cluster_name = Column(String(128), default="primary-eks-cluster")
    change_timestamp = Column(String(64), default="Just now")

    before_cpu_request = Column(String(32), default="")
    after_cpu_request = Column(String(32), default="")
    before_memory_request = Column(String(32), default="")
    after_memory_request = Column(String(32), default="")

    before_cpu_util_pct = Column(Float, default=0.0)
    after_cpu_util_pct = Column(Float, default=0.0)
    before_memory_util_pct = Column(Float, default=0.0)
    after_memory_util_pct = Column(Float, default=0.0)

    oom_kills_before = Column(Integer, default=0)
    oom_kills_after = Column(Integer, default=0)
    restarts_before = Column(Integer, default=0)
    restarts_after = Column(Integer, default=0)

    monthly_savings_achieved = Column(Float, default=0.0)
    status = Column(String(64), default="Successful Optimization")
    recommendation_id = Column(String(64), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SettingsModel(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    safety_margin_pct = Column(Float, default=20.0)
    min_observation_days = Column(Integer, default=7)
    auto_approve_min_confidence = Column(String(16), default="High")
    prometheus_url = Column(String(255), default="http://prometheus.monitoring.svc.cluster.local:9090")
    scrape_interval_seconds = Column(Integer, default=30)
    enable_hpa_safety_check = Column(Boolean, default=True)
    enable_vpa_conflict_check = Column(Boolean, default=True)
    api_base_url = Column(String(255), default="http://localhost:8000/api/v1")
