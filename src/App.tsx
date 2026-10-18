import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ClustersPage } from './pages/ClustersPage';
import { WorkloadsPage } from './pages/WorkloadsPage';
import { WorkloadDetailPage } from './pages/WorkloadDetailPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { RecommendationDetailPage } from './pages/RecommendationDetailPage';
import { CostOptimizationPage } from './pages/CostOptimizationPage';
import { AlertsPage } from './pages/AlertsPage';
import { ChangesAuditPage } from './pages/ChangesAuditPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/overview" replace />} />
            <Route path="overview" element={<DashboardPage />} />
            <Route path="clusters" element={<ClustersPage />} />
            <Route path="workloads" element={<WorkloadsPage />} />
            <Route path="workloads/:id" element={<WorkloadDetailPage />} />
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="recommendations/:id" element={<RecommendationDetailPage />} />
            <Route path="cost-optimization" element={<CostOptimizationPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="changes-audit" element={<ChangesAuditPage />} />
            <Route path="evaluation" element={<EvaluationPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
};

export default App;
