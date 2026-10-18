import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { DataQualityBadge } from '../components/common/DataQualityBadge';
import { ProvisioningStatus, WorkloadType } from '../types';

export const WorkloadsPage: React.FC = () => {
  const navigate = useNavigate();
  const { workloads, refreshData } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNamespace, setSelectedNamespace] = useState('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  const namespaces = Array.from(new Set(workloads.map((w) => w.namespace)));

  const filteredWorkloads = workloads.filter((w) => {
    const matchesSearch =
      w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      w.namespace.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesNs = selectedNamespace === 'all' || w.namespace === selectedNamespace;
    const matchesType = selectedType === 'all' || w.type === selectedType;
    const matchesStatus = selectedStatus === 'all' || w.status === selectedStatus;

    return matchesSearch && matchesNs && matchesType && matchesStatus;
  });

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-primary-container/20 text-primary border border-primary-container/30 font-semibold">
              KUBERNETES WORKLOADS
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Workload Inventory &amp; Provisioning Status
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Inspect configured CPU/Memory requests and limits against actual continuous utilization metrics.
          </p>
        </div>

        <button
          onClick={() => refreshData()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface font-headline-sm text-headline-sm transition-all border border-surface-container-highest self-start md:self-auto"
        >
          <span className="material-symbols-outlined text-[18px]">refresh</span>
          <span>Refresh Inventory</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-space-md p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-md">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[220px]">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-on-surface-variant">
              search
            </span>
            <input
              type="text"
              placeholder="Filter workloads by name or namespace..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface placeholder-on-surface-variant text-body-sm focus:outline-none focus:border-primary-container"
            />
          </div>

          {/* Namespace Filter */}
          <select
            value={selectedNamespace}
            onChange={(e) => setSelectedNamespace(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none focus:border-primary-container"
          >
            <option value="all">All Namespaces</option>
            {namespaces.map((ns) => (
              <option key={ns} value={ns}>
                Namespace: {ns}
              </option>
            ))}
          </select>

          {/* Workload Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none focus:border-primary-container"
          >
            <option value="all">All Workload Types</option>
            <option value="Deployment">Deployment</option>
            <option value="StatefulSet">StatefulSet</option>
            <option value="DaemonSet">DaemonSet</option>
            <option value="Job">Job</option>
          </select>

          {/* Provisioning Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none focus:border-primary-container"
          >
            <option value="all">All Provisioning States</option>
            <option value="Healthy">Healthy</option>
            <option value="Over-provisioned">Over-provisioned</option>
            <option value="Under-provisioned">Under-provisioned</option>
            <option value="Warning">Warning</option>
          </select>
        </div>

        <div className="text-xs text-on-surface-variant font-mono">
          Showing <strong>{filteredWorkloads.length}</strong> of {workloads.length} Workloads
        </div>
      </div>

      {/* Workload DataTable */}
      <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-lowest/60 border-b border-surface-container-high/60 text-on-surface-variant font-label-sm text-label-sm uppercase">
                <th className="py-3.5 px-4">Workload Identity</th>
                <th className="py-3.5 px-4">Replicas</th>
                <th className="py-3.5 px-4">CPU Config</th>
                <th className="py-3.5 px-4">Memory Config</th>
                <th className="py-3.5 px-4">Utilization</th>
                <th className="py-3.5 px-4">Status &amp; Quality</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high/40 text-body-sm">
              {filteredWorkloads.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-on-surface-variant">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <span className="material-symbols-outlined text-[36px] text-on-surface-variant">layers_clear</span>
                      <p className="font-semibold text-on-surface">No workloads found</p>
                      <p className="text-xs text-on-surface-variant max-w-sm">
                        {workloads.length === 0
                          ? 'No workloads have been registered or synced in the database yet.'
                          : 'No workloads matched your search or filter settings.'}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredWorkloads.map((wl) => (
                <tr key={wl.id} className="hover:bg-surface-container-high/40 transition-colors">
                  {/* Identity */}
                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span
                        onClick={() => navigate(`/workloads/${wl.id}`)}
                        className="font-semibold text-on-surface hover:text-primary cursor-pointer transition-colors"
                      >
                        {wl.name}
                      </span>
                      <span className="text-xs text-on-surface-variant">
                        {wl.namespace} · <span className="font-mono">{wl.type}</span>
                      </span>
                    </div>
                  </td>

                  {/* Replicas */}
                  <td className="py-4 px-4">
                    <span className="font-mono text-xs font-medium text-on-surface">
                      {wl.replicasAvailable} / {wl.replicasDesired} Pods
                    </span>
                  </td>

                  {/* CPU Config */}
                  <td className="py-4 px-4 font-mono text-xs">
                    <div className="flex flex-col">
                      <span className="text-on-surface">Req: {wl.cpuRequest}</span>
                      <span className="text-on-surface-variant">Limit: {wl.cpuLimit}</span>
                    </div>
                  </td>

                  {/* Memory Config */}
                  <td className="py-4 px-4 font-mono text-xs">
                    <div className="flex flex-col">
                      <span className="text-on-surface">Req: {wl.memoryRequestMb} MB</span>
                      <span className="text-on-surface-variant">Limit: {wl.memoryLimitMb} MB</span>
                    </div>
                  </td>

                  {/* Utilization */}
                  <td className="py-4 px-4">
                    <div className="space-y-1.5 w-36">
                      <div>
                        <div className="flex justify-between text-[11px] font-mono text-on-surface-variant mb-0.5">
                          <span>CPU</span>
                          <span className="text-on-surface">{wl.cpuUtilizationPct.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              wl.cpuUtilizationPct > 85 ? 'bg-error' : 'bg-primary-container'
                            }`}
                            style={{ width: `${Math.min(wl.cpuUtilizationPct, 100)}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] font-mono text-on-surface-variant mb-0.5">
                          <span>Memory</span>
                          <span className="text-on-surface">{wl.memoryUtilizationPct.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              wl.memoryUtilizationPct > 85 ? 'bg-error' : 'bg-tertiary'
                            }`}
                            style={{ width: `${Math.min(wl.memoryUtilizationPct, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Status & Data Quality */}
                  <td className="py-4 px-4">
                    <div className="flex flex-col gap-1.5 items-start">
                      <StatusBadge status={wl.status} size="sm" />
                      <DataQualityBadge status={wl.dataQualityStatus} />
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => navigate(`/workloads/${wl.id}`)}
                      className="px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface text-xs font-medium border border-surface-container-highest transition-colors"
                    >
                      Inspect Details
                    </button>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
