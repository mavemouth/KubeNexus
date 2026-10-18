-- ====================================================================
-- KubeNexus: Supabase / PostgreSQL Database Schema
-- ====================================================================
-- You can copy-paste and run this entire script directly into the
-- Supabase SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- ====================================================================

-- 1. Clusters Table
CREATE TABLE IF NOT EXISTS clusters (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    environment VARCHAR(32) DEFAULT 'production',
    connection_status VARCHAR(32) DEFAULT 'Connected',
    last_checked VARCHAR(64) DEFAULT 'Just now',
    workload_count INTEGER DEFAULT 0,
    monitoring_status VARCHAR(32) DEFAULT 'Healthy',
    node_count INTEGER DEFAULT 3,
    k8s_version VARCHAR(32) DEFAULT 'v1.28.2',
    provider VARCHAR(64) DEFAULT 'AWS EKS',
    api_endpoint VARCHAR(255) DEFAULT 'https://api.k8s.local',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Workloads Table
CREATE TABLE IF NOT EXISTS workloads (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    namespace VARCHAR(64) NOT NULL,
    cluster_id VARCHAR(64) REFERENCES clusters(id) ON DELETE SET NULL,
    cluster_name VARCHAR(128) NOT NULL,
    type VARCHAR(32) DEFAULT 'Deployment',
    replicas_desired INTEGER DEFAULT 1,
    replicas_available INTEGER DEFAULT 1,
    cpu_request VARCHAR(32) DEFAULT '1.0 Core',
    cpu_limit VARCHAR(32) DEFAULT '2.0 Cores',
    cpu_request_cores DOUBLE PRECISION DEFAULT 1.0,
    cpu_limit_cores DOUBLE PRECISION DEFAULT 2.0,
    cpu_usage_cores DOUBLE PRECISION DEFAULT 0.5,
    memory_request_mb DOUBLE PRECISION DEFAULT 1024.0,
    memory_limit_mb DOUBLE PRECISION DEFAULT 2048.0,
    cpu_utilization_pct DOUBLE PRECISION DEFAULT 50.0,
    memory_utilization_pct DOUBLE PRECISION DEFAULT 50.0,
    status VARCHAR(32) DEFAULT 'Healthy',
    data_quality_status VARCHAR(32) DEFAULT 'valid',
    restarts INTEGER DEFAULT 0,
    oom_kills INTEGER DEFAULT 0,
    throttling_count INTEGER DEFAULT 0,
    last_analysis_time VARCHAR(64) DEFAULT 'Just now',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(64) PRIMARY KEY,
    workload_id VARCHAR(64) NOT NULL,
    workload_name VARCHAR(128) NOT NULL,
    namespace VARCHAR(64) NOT NULL,
    cluster_name VARCHAR(128) NOT NULL,
    workload_type VARCHAR(32) DEFAULT 'Deployment',
    
    current_cpu_request VARCHAR(32) DEFAULT '1.0 Core',
    recommended_cpu_request VARCHAR(32) DEFAULT '1.0 Core',
    current_cpu_limit VARCHAR(32) DEFAULT '2.0 Cores',
    recommended_cpu_limit VARCHAR(32) DEFAULT '2.0 Cores',
    
    current_memory_request VARCHAR(32) DEFAULT '1.0 GB',
    recommended_memory_request VARCHAR(32) DEFAULT '1.0 GB',
    current_memory_limit VARCHAR(32) DEFAULT '2.0 GB',
    recommended_memory_limit VARCHAR(32) DEFAULT '2.0 GB',
    
    observation_window VARCHAR(64) DEFAULT '7-day continuous analysis',
    evidence_reason TEXT DEFAULT '',
    assumptions TEXT DEFAULT '',
    risk_level VARCHAR(16) DEFAULT 'Low',
    confidence VARCHAR(16) DEFAULT 'High',
    estimated_monthly_savings DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'Generated',
    created_at VARCHAR(64) DEFAULT 'Just now',
    expires_at VARCHAR(64) DEFAULT 'In 7 days',
    
    hpa_detected BOOLEAN DEFAULT FALSE,
    vpa_detected BOOLEAN DEFAULT FALSE,
    data_quality_check_passed BOOLEAN DEFAULT TRUE,
    metrics_fresh BOOLEAN DEFAULT TRUE,
    percentiles_json TEXT DEFAULT '{}'
);

-- 4. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(64) PRIMARY KEY,
    severity VARCHAR(16) DEFAULT 'Info',
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    affected_workload VARCHAR(128) DEFAULT '',
    cluster_name VARCHAR(128) DEFAULT '',
    timestamp VARCHAR(64) DEFAULT 'Just now',
    status VARCHAR(32) DEFAULT 'Active',
    category VARCHAR(32) DEFAULT 'Utilization',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Audit Events Table
CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR(64) PRIMARY KEY,
    timestamp VARCHAR(64) DEFAULT 'Just now',
    workload_name VARCHAR(128) NOT NULL,
    namespace VARCHAR(64) DEFAULT 'production',
    cluster_name VARCHAR(128) DEFAULT 'primary-eks-cluster',
    previous_cpu_request VARCHAR(32) DEFAULT '',
    new_cpu_request VARCHAR(32) DEFAULT '',
    previous_memory_request VARCHAR(32) DEFAULT '',
    new_memory_request VARCHAR(32) DEFAULT '',
    changed_by VARCHAR(128) DEFAULT 'Alex M.',
    user_role VARCHAR(128) DEFAULT 'DevOps Engineer',
    action VARCHAR(32) DEFAULT 'Approved',
    recommendation_id VARCHAR(64) DEFAULT '',
    status VARCHAR(32) DEFAULT 'Completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Post-Change Evaluations Table
CREATE TABLE IF NOT EXISTS evaluations (
    id VARCHAR(64) PRIMARY KEY,
    workload_id VARCHAR(64) NOT NULL,
    workload_name VARCHAR(128) NOT NULL,
    namespace VARCHAR(64) DEFAULT 'production',
    cluster_name VARCHAR(128) DEFAULT 'primary-eks-cluster',
    change_timestamp VARCHAR(64) DEFAULT 'Just now',
    
    before_cpu_request VARCHAR(32) DEFAULT '',
    after_cpu_request VARCHAR(32) DEFAULT '',
    before_memory_request VARCHAR(32) DEFAULT '',
    after_memory_request VARCHAR(32) DEFAULT '',
    
    before_cpu_util_pct DOUBLE PRECISION DEFAULT 0.0,
    after_cpu_util_pct DOUBLE PRECISION DEFAULT 0.0,
    before_memory_util_pct DOUBLE PRECISION DEFAULT 0.0,
    after_memory_util_pct DOUBLE PRECISION DEFAULT 0.0,
    
    oom_kills_before INTEGER DEFAULT 0,
    oom_kills_after INTEGER DEFAULT 0,
    restarts_before INTEGER DEFAULT 0,
    restarts_after INTEGER DEFAULT 0,
    
    monthly_savings_achieved DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(64) DEFAULT 'Successful Optimization',
    recommendation_id VARCHAR(64) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Platform Settings Table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    safety_margin_pct DOUBLE PRECISION DEFAULT 20.0,
    min_observation_days INTEGER DEFAULT 7,
    auto_approve_min_confidence VARCHAR(16) DEFAULT 'High',
    prometheus_url VARCHAR(255) DEFAULT 'http://prometheus.monitoring.svc.cluster.local:9090',
    scrape_interval_seconds INTEGER DEFAULT 30,
    enable_hpa_safety_check BOOLEAN DEFAULT TRUE,
    enable_vpa_conflict_check BOOLEAN DEFAULT TRUE,
    api_base_url VARCHAR(255) DEFAULT 'http://localhost:8000/api/v1'
);

-- Ensure a default settings row exists
INSERT INTO settings (id, safety_margin_pct, min_observation_days, auto_approve_min_confidence, prometheus_url, scrape_interval_seconds, enable_hpa_safety_check, enable_vpa_conflict_check, api_base_url)
VALUES (1, 20.0, 7, 'High', 'http://prometheus.monitoring.svc.cluster.local:9090', 30, TRUE, TRUE, 'http://localhost:8000/api/v1')
ON CONFLICT (id) DO NOTHING;

-- Indexing for fast query lookups
CREATE INDEX IF NOT EXISTS idx_workloads_namespace ON workloads(namespace);
CREATE INDEX IF NOT EXISTS idx_workloads_cluster_id ON workloads(cluster_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_workload_id ON recommendations(workload_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_evaluations_workload_id ON evaluations(workload_id);
