import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Cluster } from '../types';

export const ClustersPage: React.FC = () => {
  const { clusters, addCluster, setSelectedClusterId, selectedClusterId } = useApp();
  const [modalOpen, setModalOpen] = useState(false);

  // Form State for Registering Cluster
  const [name, setName] = useState('');
  const [provider, setProvider] = useState<'AWS EKS' | 'GKE' | 'Self-Hosted Minikube' | 'Azure AKS'>('AWS EKS');
  const [environment, setEnvironment] = useState<'production' | 'staging' | 'development'>('production');
  const [apiEndpoint, setApiEndpoint] = useState('');

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    await addCluster({
      name,
      provider,
      environment,
      apiEndpoint: apiEndpoint || 'https://api.k8s.internal:6443',
      nodeCount: 4,
      workloadCount: 0
    });

    setName('');
    setApiEndpoint('');
    setModalOpen(false);
  };

  const connectedCount = clusters.filter((c) => c.connectionStatus === 'Connected').length;
  const totalNodes = clusters.reduce((acc, c) => acc + c.nodeCount, 0);
  const totalWorkloads = clusters.reduce((acc, c) => acc + c.workloadCount, 0);

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-secondary-container/30 text-secondary border border-secondary-container/40 font-semibold">
              KUBERNETES CLUSTERS
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Cluster Registry &amp; Connectivity
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Register and monitor Kubernetes cluster endpoints, node pools, and Prometheus scraping agents.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20 font-semibold self-start md:self-auto"
        >
          <span className="material-symbols-outlined text-[20px]">add</span>
          <span>Register Cluster</span>
        </button>
      </div>

      {/* Summary KPI Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-space-md">
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Registered Clusters</span>
          <span className="font-headline-xl text-headline-xl text-on-surface font-semibold mt-1">{clusters.length}</span>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Connected Telemetry</span>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-headline-xl text-headline-xl text-tertiary font-semibold">{connectedCount}</span>
            <span className="text-xs text-on-surface-variant">/ {clusters.length} online</span>
          </div>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Total Node Capacity</span>
          <span className="font-headline-xl text-headline-xl text-on-surface font-semibold mt-1">{totalNodes} Nodes</span>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Monitored Workloads</span>
          <span className="font-headline-xl text-headline-xl text-primary font-semibold mt-1">{totalWorkloads}</span>
        </div>
      </div>

      {/* Clusters Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
        {clusters.length === 0 ? (
          <div className="col-span-full p-12 rounded-xl bg-surface-container-low border border-surface-container-high/60 flex flex-col items-center justify-center text-center">
            <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-2">dns</span>
            <h3 className="font-headline-md text-headline-md font-semibold text-on-surface">No Clusters Registered</h3>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-md mt-1 mb-4">
              Your PostgreSQL database is connected. Click below to register your first Kubernetes cluster endpoint.
            </p>
            <button
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm hover:brightness-110 transition-all font-semibold"
            >
              <span className="material-symbols-outlined text-[20px]">add</span>
              <span>Register Cluster</span>
            </button>
          </div>
        ) : (
          clusters.map((c) => {
          const isSelected = c.id === selectedClusterId;
          return (
            <div
              key={c.id}
              className={`rounded-xl bg-surface-container-low/80 backdrop-blur-xl p-space-md border transition-all flex flex-col justify-between shadow-lg ${
                isSelected ? 'border-primary-container shadow-[0_0_16px_rgba(56,189,248,0.2)]' : 'border-surface-container-high/60 hover:bg-surface-container-high/40'
              }`}
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-surface-container-highest flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined text-[24px]">dns</span>
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">{c.name}</h3>
                        {isSelected && (
                          <span className="px-2 py-0.2 rounded-full bg-primary-container/20 text-primary font-label-sm text-[10px] font-bold border border-primary-container/40">
                            Active
                          </span>
                        )}
                      </div>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        {c.provider} · {c.environment}
                      </span>
                    </div>
                  </div>

                  <span className={`px-2.5 py-1 rounded-full font-label-sm text-label-sm border flex items-center gap-1.5 ${
                    c.connectionStatus === 'Connected' ? 'bg-tertiary-container/20 text-tertiary border-tertiary-container/40' :
                    c.connectionStatus === 'Degraded' ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' :
                    'bg-error-container/30 text-error border-error-container/50'
                  }`}>
                    <span className={`h-2 w-2 rounded-full ${c.connectionStatus === 'Connected' ? 'bg-tertiary animate-pulse' : 'bg-error'}`} />
                    <span>{c.connectionStatus}</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-surface-container-high/50 font-body-sm text-body-sm">
                  <div>
                    <span className="text-on-surface-variant text-xs">API Endpoint:</span>
                    <p className="font-mono text-on-surface text-xs truncate mt-0.5">{c.apiEndpoint}</p>
                  </div>
                  <div>
                    <span className="text-on-surface-variant text-xs">Kubernetes Version:</span>
                    <p className="font-mono text-on-surface text-xs mt-0.5">{c.k8sVersion}</p>
                  </div>
                  <div>
                    <span className="text-on-surface-variant text-xs">Node Pool:</span>
                    <p className="font-medium text-on-surface mt-0.5">{c.nodeCount} Worker Nodes</p>
                  </div>
                  <div>
                    <span className="text-on-surface-variant text-xs">Last Health Check:</span>
                    <p className="text-on-surface mt-0.5">{c.lastChecked}</p>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-surface-container-high/60 flex items-center justify-between">
                <span className="text-xs text-on-surface-variant">
                  Monitoring Agent: <strong className="text-tertiary font-medium">{c.monitoringStatus}</strong>
                </span>
                <button
                  onClick={() => setSelectedClusterId(c.id)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                    isSelected
                      ? 'bg-primary-container/20 text-primary border-primary-container/40'
                      : 'bg-surface-container-high hover:bg-surface-bright text-on-surface border-surface-container-highest'
                  }`}
                >
                  {isSelected ? 'Active Selection' : 'Select Cluster'}
                </button>
              </div>
            </div>
          );
        }))}
      </div>

      {/* Register Cluster Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-xl bg-surface-container-low border border-surface-container-highest p-space-lg shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container-high">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-primary">add_circle</span>
                <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
                  Register Kubernetes Cluster
                </h2>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-1">
                  Cluster Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. k8s-prod-us-east"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface focus:outline-none focus:border-primary-container text-body-md"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1">
                    Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface focus:outline-none focus:border-primary-container text-body-md"
                  >
                    <option value="AWS EKS">AWS EKS</option>
                    <option value="GKE">GKE</option>
                    <option value="Self-Hosted Minikube">Self-Hosted Minikube</option>
                    <option value="Azure AKS">Azure AKS</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1">
                    Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface focus:outline-none focus:border-primary-container text-body-md"
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-1">
                  API Server Endpoint URL
                </label>
                <input
                  type="url"
                  placeholder="https://eks-prod-us-east-1.amazonaws.com"
                  value={apiEndpoint}
                  onChange={(e) => setApiEndpoint(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface focus:outline-none focus:border-primary-container text-body-md font-mono text-xs"
                />
              </div>

              <div className="pt-3 border-t border-surface-container-high flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface text-body-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-semibold hover:brightness-110 text-body-sm shadow-md"
                >
                  Connect &amp; Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
