from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# Core Enums & Literals matching frontend TypeScript types
ConnectionStatus = Literal['Connected', 'Degraded', 'Disconnected', 'Monitoring Unavailable']
WorkloadType = Literal['Deployment', 'StatefulSet', 'DaemonSet', 'Job']
ProvisioningStatus = Literal['Healthy', 'Over-provisioned', 'Under-provisioned', 'Warning', 'Critical']
DataQualityStatus = Literal['valid', 'insufficient_evidence', 'stale_data', 'monitoring_unavailable', 'invalid_data']
RecommendationStatus = Literal['Generated', 'Reviewed', 'Approved', 'Applied', 'Evaluated', 'Rejected', 'Expired']
RiskLevel = Literal['Low', 'Medium', 'High']
ConfidenceLevel = Literal['High', 'Medium', 'Low']
AlertSeverity = Literal['Critical', 'Warning', 'Info']
AuditAction = Literal['Approved', 'Rejected', 'Applied', 'Failed', 'Rolled Back']
AuthMethod = Literal['local', 'kubeconfig', 'token']

class ClusterBase(BaseModel):
    name: str
    environment: Literal['production', 'staging', 'development'] = 'production'
    connectionStatus: ConnectionStatus = 'Connected'
    lastChecked: str = 'Just now'
    workloadCount: int = 0
    monitoringStatus: Literal['Healthy', 'Degraded', 'Unavailable'] = 'Healthy'
    nodeCount: int = 3
    k8sVersion: str = 'v1.28.2'
    provider: Literal['AWS EKS', 'GKE', 'Self-Hosted Minikube', 'Azure AKS'] = 'AWS EKS'
    apiEndpoint: str = 'https://api.k8s.local'
    authMethod: AuthMethod = 'local'
    prometheusUrl: str = 'http://localhost:9090'

class ClusterCreate(BaseModel):
    name: str
    environment: Optional[Literal['production', 'staging', 'development']] = 'production'
    provider: Optional[Literal['AWS EKS', 'GKE', 'Self-Hosted Minikube', 'Azure AKS']] = 'AWS EKS'
    apiEndpoint: Optional[str] = None
    nodeCount: Optional[int] = None
    authMethod: Optional[AuthMethod] = 'local'
    kubeconfigRaw: Optional[str] = None
    bearerToken: Optional[str] = None
    prometheusUrl: Optional[str] = 'http://localhost:9090'

class Cluster(ClusterBase):
    id: str

class MetricTimeSeriesPoint(BaseModel):
    timestamp: str
    cpuUsage: float # cores
    cpuRequest: float # cores
    cpuLimit: float # cores
    memoryUsageMb: float # MB
    memoryLimitMb: float # MB

class Workload(BaseModel):
    id: str
    name: str
    namespace: str
    clusterId: str
    clusterName: str
    type: WorkloadType
    replicasDesired: int
    replicasAvailable: int
    cpuRequest: str # e.g. "2.0 Cores"
    cpuLimit: str # e.g. "4.0 Cores"
    cpuRequestCores: float
    cpuLimitCores: float
    cpuUsageCores: float
    memoryRequestMb: float
    memoryLimitMb: float
    cpuUtilizationPct: float
    memoryUtilizationPct: float
    status: ProvisioningStatus
    dataQualityStatus: DataQualityStatus
    restarts: int
    oomKills: int
    throttlingCount: int
    lastAnalysisTime: str

class Percentiles(BaseModel):
    p50Cpu: float
    p90Cpu: float
    p99Cpu: float
    maxCpu: float
    p50MemoryMb: float
    p90MemoryMb: float
    p99MemoryMb: float
    maxMemoryMb: float

class Recommendation(BaseModel):
    id: str
    workloadId: str
    workloadName: str
    namespace: str
    clusterName: str
    workloadType: WorkloadType
    
    currentCpuRequest: str
    recommendedCpuRequest: str
    currentCpuLimit: str
    recommendedCpuLimit: str
    
    currentMemoryRequest: str
    recommendedMemoryRequest: str
    currentMemoryLimit: str
    recommendedMemoryLimit: str
    
    observationWindow: str # e.g. "14-day continuous analysis"
    evidenceReason: str
    assumptions: str
    riskLevel: RiskLevel
    confidence: ConfidenceLevel
    estimatedMonthlySavings: float # in USD
    status: RecommendationStatus
    createdAt: str
    expiresAt: str
    
    hpaDetected: bool = False
    vpaDetected: bool = False
    dataQualityCheckPassed: bool = True
    metricsFresh: bool = True
    
    percentiles: Percentiles

class AlertItem(BaseModel):
    id: str
    severity: AlertSeverity
    title: str
    description: str
    affectedWorkload: str
    clusterName: str
    timestamp: str
    status: Literal['Active', 'Acknowledged', 'Resolved']
    category: Literal['Utilization', 'Provisioning', 'Data Quality', 'Recommendation', 'Audit']

class AuditEvent(BaseModel):
    id: str
    timestamp: str
    workloadName: str
    namespace: str
    clusterName: str
    previousCpuRequest: str
    newCpuRequest: str
    previousMemoryRequest: str
    newMemoryRequest: str
    changedBy: str
    userRole: str
    action: AuditAction
    recommendationId: str
    status: Literal['Completed', 'Pending', 'Failed']

class PostChangeEvaluation(BaseModel):
    id: str
    workloadId: str
    workloadName: str
    namespace: str
    clusterName: str
    changeTimestamp: str
    
    beforeCpuRequest: str
    afterCpuRequest: str
    beforeMemoryRequest: str
    afterMemoryRequest: str
    
    beforeCpuUtilPct: float
    afterCpuUtilPct: float
    beforeMemoryUtilPct: float
    afterMemoryUtilPct: float
    
    oomKillsBefore: int
    oomKillsAfter: int
    restartsBefore: int
    restartsAfter: int
    
    monthlySavingsAchieved: float
    status: Literal['Successful Optimization', 'Under Review', 'Rolled Back']
    recommendationId: str

class OptimizationSettings(BaseModel):
    safetyMarginPct: float = 20.0
    minObservationDays: int = 7
    autoApproveMinConfidence: ConfidenceLevel = 'High'
    prometheusUrl: str = 'http://prometheus.monitoring.svc.cluster.local:9090'
    scrapeIntervalSeconds: int = 30
    enableHpaSafetyCheck: bool = True
    enableVpaConflictCheck: bool = True
    apiBaseUrl: str = 'http://localhost:8000/api/v1'

class AnalysisResponse(BaseModel):
    status: str
    message: str
    workloadId: str
    recommendation: Optional[Recommendation] = None
    provisioningStatus: ProvisioningStatus
    utilizationDetails: Dict[str, Any]

class CostOptimizationSummary(BaseModel):
    monthlySpend: float
    potentialSavings: float
    optimizedSpend: float
    savingsPct: float
    overProvisionedCount: int
    underProvisionedCount: int
