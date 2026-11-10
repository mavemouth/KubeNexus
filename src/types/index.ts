export type ConnectionStatus = 'Connected' | 'Degraded' | 'Disconnected' | 'Monitoring Unavailable';
export type WorkloadType = 'Deployment' | 'StatefulSet' | 'DaemonSet' | 'Job';
export type ProvisioningStatus = 'Healthy' | 'Over-provisioned' | 'Under-provisioned' | 'Warning' | 'Critical';
export type DataQualityStatus = 'valid' | 'insufficient_evidence' | 'stale_data' | 'monitoring_unavailable' | 'invalid_data';
export type RecommendationStatus = 'Generated' | 'Reviewed' | 'Approved' | 'Applied' | 'Evaluated' | 'Rejected' | 'Expired' | 'Rolled Back';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type ConfidenceLevel = 'High' | 'Medium' | 'Low';
export type AlertSeverity = 'Critical' | 'Warning' | 'Info';
export type AuditAction = 'Approved' | 'Rejected' | 'Applied' | 'Failed' | 'Rolled Back';

export interface Cluster {
  id: string;
  name: string;
  environment: 'production' | 'staging' | 'development';
  connectionStatus: ConnectionStatus;
  lastChecked: string;
  workloadCount: number;
  monitoringStatus: 'Healthy' | 'Degraded' | 'Unavailable';
  nodeCount: number;
  k8sVersion: string;
  provider: 'AWS EKS' | 'GKE' | 'Self-Hosted Minikube' | 'Azure AKS';
  apiEndpoint: string;
  authMethod?: 'local' | 'kubeconfig' | 'token' | 'demo';
  prometheusUrl?: string;
}

export interface ClusterCreatePayload {
  name: string;
  environment?: 'production' | 'staging' | 'development';
  provider?: 'AWS EKS' | 'GKE' | 'Self-Hosted Minikube' | 'Azure AKS';
  apiEndpoint?: string;
  authMethod?: 'local' | 'kubeconfig' | 'token' | 'demo';
  kubeconfigRaw?: string;
  bearerToken?: string;
  prometheusUrl?: string;
  workloadCount?: number;
}

export interface MetricTimeSeriesPoint {
  timestamp: string;
  cpuUsage: number; // cores
  cpuRequest: number; // cores
  cpuLimit: number; // cores
  memoryUsageMb: number; // MB
  memoryLimitMb: number; // MB
}

export interface Workload {
  id: string;
  name: string;
  namespace: string;
  clusterId: string;
  clusterName: string;
  type: WorkloadType;
  replicasDesired: number;
  replicasAvailable: number;
  cpuRequest: string; // e.g. "2 cores" or "500m"
  cpuLimit: string; // e.g. "4 cores"
  cpuRequestCores: number;
  cpuLimitCores: number;
  cpuUsageCores: number;
  memoryRequestMb: number;
  memoryLimitMb: number;
  cpuUtilizationPct: number;
  memoryUtilizationPct: number;
  status: ProvisioningStatus;
  dataQualityStatus: DataQualityStatus;
  restarts: number;
  oomKills: number;
  throttlingCount: number;
  lastAnalysisTime: string;
}

export interface Recommendation {
  id: string;
  workloadId: string;
  workloadName: string;
  namespace: string;
  clusterName: string;
  workloadType: WorkloadType;
  
  currentCpuRequest: string;
  recommendedCpuRequest: string;
  currentCpuLimit: string;
  recommendedCpuLimit: string;
  
  currentMemoryRequest: string;
  recommendedMemoryRequest: string;
  currentMemoryLimit: string;
  recommendedMemoryLimit: string;
  
  observationWindow: string; // e.g. "14-day continuous analysis"
  evidenceReason: string;
  assumptions: string;
  riskLevel: RiskLevel;
  confidence: ConfidenceLevel;
  estimatedMonthlySavings: number; // in USD
  status: RecommendationStatus;
  createdAt: string;
  expiresAt: string;
  
  hpaDetected: boolean;
  vpaDetected: boolean;
  dataQualityCheckPassed: boolean;
  metricsFresh: boolean;
  
  percentiles: {
    p50Cpu: number;
    p90Cpu: number;
    p99Cpu: number;
    maxCpu: number;
    p50MemoryMb: number;
    p90MemoryMb: number;
    p99MemoryMb: number;
    maxMemoryMb: number;
  };
}

export interface AlertItem {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  affectedWorkload: string;
  clusterName: string;
  timestamp: string;
  status: 'Active' | 'Acknowledged' | 'Resolved';
  category: 'Utilization' | 'Provisioning' | 'Data Quality' | 'Recommendation' | 'Audit';
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  workloadName: string;
  namespace: string;
  clusterName: string;
  previousCpuRequest: string;
  newCpuRequest: string;
  previousMemoryRequest: string;
  newMemoryRequest: string;
  changedBy: string;
  userRole: string;
  action: AuditAction;
  recommendationId: string;
  status: 'Completed' | 'Pending' | 'Failed';
}

export interface PostChangeEvaluation {
  id: string;
  workloadId: string;
  workloadName: string;
  namespace: string;
  clusterName: string;
  changeTimestamp: string;
  
  beforeCpuRequest: string;
  afterCpuRequest: string;
  beforeMemoryRequest: string;
  afterMemoryRequest: string;
  
  beforeCpuUtilPct: number;
  afterCpuUtilPct: number;
  beforeMemoryUtilPct: number;
  afterMemoryUtilPct: number;
  
  oomKillsBefore: number;
  oomKillsAfter: number;
  restartsBefore: number;
  restartsAfter: number;
  
  monthlySavingsAchieved: number;
  status: 'Successful Optimization' | 'Under Review' | 'Rolled Back';
  recommendationId: string;
}

export interface OptimizationSettings {
  safetyMarginPct: number;
  minObservationDays: number;
  autoApproveMinConfidence: ConfidenceLevel;
  prometheusUrl: string;
  scrapeIntervalSeconds: number;
  enableHpaSafetyCheck: boolean;
  enableVpaConflictCheck: boolean;
  apiBaseUrl: string;
}

export interface CostOptimizationSummary {
  monthlySpend: number;
  potentialSavings: number;
  optimizedSpend: number;
  savingsPct: number;
  overProvisionedCount: number;
  underProvisionedCount: number;
}

