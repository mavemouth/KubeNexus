import {
  Cluster,
  ClusterCreatePayload,
  Workload,
  Recommendation,
  AlertItem,
  AuditEvent,
  PostChangeEvaluation,
  MetricTimeSeriesPoint,
  OptimizationSettings
} from '../types';

import {
  INITIAL_CLUSTERS,
  INITIAL_WORKLOADS,
  INITIAL_RECOMMENDATIONS,
  INITIAL_ALERTS,
  INITIAL_AUDIT_EVENTS,
  INITIAL_EVALUATIONS,
  MOCK_TELEMETRY_SERIES,
  INITIAL_SETTINGS
} from '../mock';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Safe fetcher connecting directly to FastAPI + PostgreSQL backend
async function fetchOrFallback<T>(url: string, fallback: T, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, options);
    if (!response.ok) {
      console.warn(`API call ${url} returned ${response.status}.`);
      return fallback;
    }
    return await response.json();
  } catch (error) {
    console.warn(`API call ${url} error:`, error);
    return fallback;
  }
}

export const api = {
  // Clusters API
  getClusters: (): Promise<Cluster[]> => {
    return fetchOrFallback('/clusters', INITIAL_CLUSTERS);
  },
  
  createCluster: async (clusterData: ClusterCreatePayload | Partial<Cluster>): Promise<Cluster> => {
    const response = await fetch(`${API_BASE_URL}/clusters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(clusterData)
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Cluster connection failed (${response.status})`);
    }
    return await response.json();
  },

  // Workloads API
  getWorkloads: (clusterId?: string): Promise<Workload[]> => {
    const path = clusterId ? `/workloads?clusterId=${encodeURIComponent(clusterId)}` : '/workloads';
    return fetchOrFallback(path, INITIAL_WORKLOADS);
  },

  getWorkloadById: async (id: string): Promise<Workload | undefined> => {
    try {
      const res = await fetch(`${API_BASE_URL}/workloads/${id}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch workload ${id}:`, e);
    }
    return undefined;
  },

  getWorkloadMetrics: (id: string, timeRange = '24h'): Promise<MetricTimeSeriesPoint[]> => {
    return fetchOrFallback(`/workloads/${id}/metrics?range=${timeRange}`, MOCK_TELEMETRY_SERIES);
  },

  runWorkloadAnalysis: async (id: string): Promise<{ status: string; message: string; recommendation?: Recommendation }> => {
    try {
      const res = await fetch(`${API_BASE_URL}/workloads/${id}/analysis`, { method: 'POST' });
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to analyze workload ${id}:`, e);
    }
    return {
      status: 'error',
      message: 'Failed to run analysis on workload.'
    };
  },

  // Recommendations API
  getRecommendations: (): Promise<Recommendation[]> => {
    return fetchOrFallback('/recommendations', INITIAL_RECOMMENDATIONS);
  },

  getRecommendationById: async (id: string): Promise<Recommendation | undefined> => {
    try {
      const res = await fetch(`${API_BASE_URL}/recommendations/${id}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch recommendation ${id}:`, e);
    }
    return undefined;
  },

  approveRecommendation: async (id: string): Promise<Recommendation> => {
    const res = await fetch(`${API_BASE_URL}/recommendations/${id}/approve`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to approve recommendation ${id}`);
    return await res.json();
  },

  rejectRecommendation: async (id: string): Promise<Recommendation> => {
    const res = await fetch(`${API_BASE_URL}/recommendations/${id}/reject`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to reject recommendation ${id}`);
    return await res.json();
  },

  applyRecommendation: async (id: string): Promise<Recommendation> => {
    const res = await fetch(`${API_BASE_URL}/recommendations/${id}/apply`, { method: 'POST' });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to apply recommendation ${id}`);
    }
    return await res.json();
  },

  // Alerts API
  getAlerts: (): Promise<AlertItem[]> => {
    return fetchOrFallback('/alerts', INITIAL_ALERTS);
  },

  resolveAlert: async (id: string): Promise<AlertItem> => {
    const res = await fetch(`${API_BASE_URL}/alerts/${id}/resolve`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to resolve alert ${id}`);
    return await res.json();
  },

  acknowledgeAlert: async (id: string): Promise<AlertItem> => {
    const res = await fetch(`${API_BASE_URL}/alerts/${id}/acknowledge`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to acknowledge alert ${id}`);
    return await res.json();
  },

  // Audit Events API
  getAuditEvents: (): Promise<AuditEvent[]> => {
    return fetchOrFallback('/audit-events', INITIAL_AUDIT_EVENTS);
  },

  // Evaluation API
  getEvaluations: (): Promise<PostChangeEvaluation[]> => {
    return fetchOrFallback('/evaluations', INITIAL_EVALUATIONS);
  },

  // Settings API
  getSettings: (): Promise<OptimizationSettings> => {
    return fetchOrFallback('/settings', INITIAL_SETTINGS);
  },

  updateSettings: async (newSettings: Partial<OptimizationSettings>): Promise<OptimizationSettings> => {
    try {
      const res = await fetch(`${API_BASE_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.error('Failed to update settings:', e);
    }
    return { ...INITIAL_SETTINGS, ...newSettings };
  },

  // Real-time SSE Alerts Stream
  subscribeAlertsStream: (onMessage: (event: any) => void): (() => void) => {
    const url = `${API_BASE_URL}/alerts/stream`;
    try {
      const eventSource = new EventSource(url);
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch {
          // Heartbeat or plain text
        }
      };
      eventSource.onerror = (err) => {
        console.warn('Alerts EventSource disconnected, reconnecting...', err);
      };
      return () => {
        eventSource.close();
      };
    } catch (e) {
      console.warn('EventSource not supported or failed to connect:', e);
      return () => {};
    }
  },

  subscribeNotifications: (onMessage: (event: any) => void): (() => void) => {
    return api.subscribeAlertsStream(onMessage);
  }
};
