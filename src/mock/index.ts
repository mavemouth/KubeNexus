import {
  Cluster,
  Workload,
  Recommendation,
  AlertItem,
  AuditEvent,
  PostChangeEvaluation,
  OptimizationSettings,
  MetricTimeSeriesPoint
} from '../types';

// Dummy data purged. The project connects to live Supabase / PostgreSQL database.
export const INITIAL_CLUSTERS: Cluster[] = [];

export const INITIAL_WORKLOADS: Workload[] = [];

export const INITIAL_RECOMMENDATIONS: Recommendation[] = [];

export const INITIAL_ALERTS: AlertItem[] = [];

export const INITIAL_AUDIT_EVENTS: AuditEvent[] = [];

export const INITIAL_EVALUATIONS: PostChangeEvaluation[] = [];

export const MOCK_TELEMETRY_SERIES: MetricTimeSeriesPoint[] = [];

export const INITIAL_SETTINGS: OptimizationSettings = {
  safetyMarginPct: 20,
  minObservationDays: 7,
  autoApproveMinConfidence: 'High',
  prometheusUrl: 'http://prometheus.monitoring.svc.cluster.local:9090',
  scrapeIntervalSeconds: 30,
  enableHpaSafetyCheck: true,
  enableVpaConflictCheck: true,
  apiBaseUrl: 'http://localhost:8000/api/v1'
};
