import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  Cluster,
  Workload,
  Recommendation,
  AlertItem,
  AuditEvent,
  PostChangeEvaluation,
  OptimizationSettings
} from '../types';
import { api } from '../api';

interface AppContextType {
  clusters: Cluster[];
  workloads: Workload[];
  recommendations: Recommendation[];
  alerts: AlertItem[];
  auditEvents: AuditEvent[];
  evaluations: PostChangeEvaluation[];
  settings: OptimizationSettings;
  
  selectedClusterId: string;
  setSelectedClusterId: (id: string) => void;
  
  selectedTimeRange: string;
  setSelectedTimeRange: (range: string) => void;
  
  // Data Quality & Simulation Mode overrides
  simulatedState: string;
  setSimulatedState: (state: string) => void;
  
  // Handlers
  addCluster: (cluster: Partial<Cluster>) => Promise<void>;
  approveRecommendation: (id: string) => Promise<void>;
  rejectRecommendation: (id: string) => Promise<void>;
  applyRecommendation: (id: string) => Promise<void>;
  resolveAlert: (id: string) => void;
  updateSettings: (newSettings: Partial<OptimizationSettings>) => void;
  runAnalysis: (id: string) => Promise<void>;
  refreshData: () => Promise<void>;
  loading: boolean;
  toastMessage: string | null;
  setToastMessage: (msg: string | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [evaluations, setEvaluations] = useState<PostChangeEvaluation[]>([]);
  const [settings, setSettings] = useState<OptimizationSettings>({} as OptimizationSettings);
  
  const [selectedClusterId, setSelectedClusterId] = useState<string>('cluster-1');
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('Last 24 Hours');
  const [simulatedState, setSimulatedState] = useState<string>('normal');
  const [loading, setLoading] = useState<boolean>(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      const [c, w, r, a, audit, ev, s] = await Promise.all([
        api.getClusters(),
        api.getWorkloads(),
        api.getRecommendations(),
        api.getAlerts(),
        api.getAuditEvents(),
        api.getEvaluations(),
        api.getSettings()
      ]);
      setClusters(c);
      setWorkloads(w);
      setRecommendations(r);
      setAlerts(a);
      setAuditEvents(audit);
      setEvaluations(ev);
      setSettings(s);
    } catch (err) {
      console.error('Error fetching application data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    const unsubscribe = api.subscribeNotifications((event) => {
      if (event.type === 'NEW_ALERT') {
        showToast(`⚠️ Alert: ${event.alert?.title || 'New anomaly detected'}`);
        refreshData();
      } else if (event.type === 'RECOMMENDATION_GENERATED') {
        showToast(`💡 New Recommendation for ${event.recommendation?.workloadName}`);
        refreshData();
      } else if (event.type === 'RECOMMENDATION_APPLIED') {
        showToast(`🚀 ${event.message || 'Optimization applied'}`);
        refreshData();
      } else if (event.type === 'ALERT_RESOLVED') {
        refreshData();
      }
    });
    return () => unsubscribe();
  }, []);

  const addCluster = async (clusterData: Partial<Cluster>) => {
    const newCluster = await api.createCluster(clusterData);
    setClusters((prev) => [newCluster, ...prev]);
    showToast(`Cluster "${newCluster.name}" registered successfully.`);
    refreshData();
  };

  const approveRecommendation = async (id: string) => {
    const updatedRec = await api.approveRecommendation(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'Approved' } : r))
    );
    showToast(`Recommendation ${id} approved.`);
    refreshData();
  };

  const rejectRecommendation = async (id: string) => {
    const updatedRec = await api.rejectRecommendation(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'Rejected' } : r))
    );
    showToast(`Recommendation ${id} rejected.`);
    refreshData();
  };

  const applyRecommendation = async (id: string) => {
    const targetRec = recommendations.find((r) => r.id === id);
    if (!targetRec) return;

    if (targetRec.status === 'Applied') {
      showToast(`Recommendation ${id} is already applied!`);
      return;
    }

    try {
      const updatedRec = await api.applyRecommendation(id);
      
      // Update recommendation status
      setRecommendations((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'Applied' } : r))
      );

      showToast(`Resource optimization applied for ${targetRec.workloadName}!`);
      await refreshData();
    } catch (err: any) {
      console.error('Failed to apply recommendation:', err);
      showToast(err?.message || 'Failed to apply recommendation');
    }
  };

  const resolveAlert = async (id: string) => {
    try {
      await api.resolveAlert(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'Resolved' } : a))
      );
      showToast(`Alert marked as resolved.`);
      refreshData();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const updateSettings = async (newSettings: Partial<OptimizationSettings>) => {
    try {
      const saved = await api.updateSettings(newSettings);
      setSettings(saved);
      showToast('Settings saved successfully.');
      refreshData();
    } catch (err) {
      console.error('Failed to save settings:', err);
      setSettings((prev) => ({ ...prev, ...newSettings }));
    }
  };

  const runAnalysis = async (id: string) => {
    try {
      const res = await api.runWorkloadAnalysis(id);
      showToast(res.message || 'Analysis completed');
      await refreshData();
    } catch (err) {
      console.error('Failed to run analysis:', err);
      showToast('Analysis request failed');
    }
  };

  return (
    <AppContext.Provider
      value={{
        clusters,
        workloads,
        recommendations,
        alerts,
        auditEvents,
        evaluations,
        settings,
        selectedClusterId,
        setSelectedClusterId,
        selectedTimeRange,
        setSelectedTimeRange,
        simulatedState,
        setSimulatedState,
        addCluster,
        approveRecommendation,
        rejectRecommendation,
        applyRecommendation,
        resolveAlert,
        updateSettings,
        runAnalysis,
        refreshData,
        loading,
        toastMessage,
        setToastMessage
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
