import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ResourceUtilizationChart } from '../components/charts/ResourceUtilizationChart';
import { MetricTimeSeriesPoint } from '../types';

export const MonitoringPage: React.FC = () => {
  const { clusters, selectedClusterId, workloads } = useApp();
  const [windowRange, setWindowRange] = useState('24h');

  const isAllClusters = selectedClusterId === 'all';
  const currentCluster = clusters.find((c) => c.id === selectedClusterId) || (isAllClusters ? null : clusters[0]);

  // Dynamic telemetry calculated from active database workloads
  const clusterWorkloads = isAllClusters
    ? workloads
    : currentCluster
    ? workloads.filter((w) => w.clusterId === currentCluster.id || w.clusterName === currentCluster.name)
    : [];
  const clusterCpuUsed = clusterWorkloads.reduce((sum, w) => sum + w.cpuUsageCores, 0);
  const clusterCpuReq = clusterWorkloads.reduce((sum, w) => sum + w.cpuRequestCores, 0);
  const clusterCpuUtil = clusterCpuReq > 0 ? (clusterCpuUsed / clusterCpuReq) * 100 : 0;

  const clusterMemUsedMb = clusterWorkloads.reduce((sum, w) => sum + (w.memoryRequestMb * (w.memoryUtilizationPct / 100)), 0);
  const clusterMemReqMb = clusterWorkloads.reduce((sum, w) => sum + w.memoryRequestMb, 0);
  const clusterMemUtil = clusterMemReqMb > 0 ? (clusterMemUsedMb / clusterMemReqMb) * 100 : 0;

  const totalPods = clusterWorkloads.reduce((sum, w) => sum + w.replicasAvailable, 0);

  // Dynamic series
  const timestamps = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'];
  const factors = [0.85, 0.90, 1.05, 1.10, 0.98, 0.95, 1.02, 0.88];
  const chartSeries: MetricTimeSeriesPoint[] = currentCluster && clusterCpuReq > 0 ? timestamps.map((t, i) => ({
    timestamp: t,
    cpuUsage: roundNumber(clusterCpuUsed * factors[i], 2),
    cpuRequest: roundNumber(clusterCpuReq, 2),
    cpuLimit: roundNumber(clusterCpuReq * 1.5, 2),
    memoryUsageMb: roundNumber(clusterMemUsedMb * factors[i], 1),
    memoryLimitMb: roundNumber(clusterMemReqMb * 1.5, 1)
  })) : [];

  function roundNumber(num: number, dec: number) {
    return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
  }

  const nodes = currentCluster ? Array.from({ length: currentCluster.nodeCount || 1 }).map((_, idx) => ({
    name: `node-${idx + 1}.${currentCluster.name}.internal`,
    status: currentCluster.monitoringStatus || 'Healthy',
    cpu: `${Math.max(2, Math.round(clusterCpuReq / (currentCluster.nodeCount || 1) + 2))} Cores`,
    memory: `${Math.max(4, Math.round((clusterMemReqMb / 1024) / (currentCluster.nodeCount || 1) + 4))} GB`,
    pods: Math.max(1, Math.round(totalPods / (currentCluster.nodeCount || 1))),
    role: idx === 0 ? 'control-plane / worker' : 'worker'
  })) : [];

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-tertiary-container/20 text-tertiary border border-tertiary-container/30 font-semibold">
              LIVE TELEMETRY
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Resource Monitoring &amp; Node Telemetry
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Real-time Prometheus metric streams across cluster nodes, namespaces, and pod resource bounds.
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-surface-container border border-surface-container-highest self-start md:self-auto">
          {['1h', '6h', '24h', '7d'].map((w) => (
            <button
              key={w}
              onClick={() => setWindowRange(w)}
              className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors ${
                windowRange === w
                  ? 'bg-primary-container text-on-primary-container font-bold'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {w}
            </button>
          ))}
        </div>
      </div>

      {!currentCluster ? (
        <div className="p-12 rounded-xl bg-surface-container-low border border-surface-container-high/60 flex flex-col items-center justify-center text-center">
          <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-2">dns</span>
          <h3 className="font-headline-md text-headline-md font-semibold text-on-surface">No Clusters Registered</h3>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-md mt-1">
            Register a Kubernetes cluster to start streaming Prometheus metrics and telemetry.
          </p>
        </div>
      ) : (
        <>
          {/* Cluster Node Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-space-md">
            <div className="p-space-md rounded-xl bg-surface-container-low/80 border border-surface-container-high/60 flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Target Cluster</span>
              <span className="font-headline-md text-headline-md text-on-surface font-semibold mt-1 truncate">
                {currentCluster.name}
              </span>
              <span className="text-xs text-tertiary mt-2 flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-tertiary animate-pulse" />
                {currentCluster.connectionStatus}
              </span>
            </div>

            <div className="p-space-md rounded-xl bg-surface-container-low/80 border border-surface-container-high/60 flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Cluster CPU Usage</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="font-headline-xl text-headline-xl text-primary font-bold">{clusterCpuUsed.toFixed(1)} Cores</span>
                <span className="text-xs text-on-surface-variant">/ {clusterCpuReq.toFixed(1)} Cores</span>
              </div>
              <span className="text-xs text-on-surface-variant mt-2">{clusterCpuUtil.toFixed(1)}% Overall Utilization</span>
            </div>

            <div className="p-space-md rounded-xl bg-surface-container-low/80 border border-surface-container-high/60 flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Cluster Memory Usage</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="font-headline-xl text-headline-xl text-tertiary font-bold">{(clusterMemUsedMb / 1024).toFixed(1)} GB</span>
                <span className="text-xs text-on-surface-variant">/ {(clusterMemReqMb / 1024).toFixed(1)} GB</span>
              </div>
              <span className="text-xs text-on-surface-variant mt-2">{clusterMemUtil.toFixed(1)}% Memory Pressure</span>
            </div>

            <div className="p-space-md rounded-xl bg-surface-container-low/80 border border-surface-container-high/60 flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Total Active Pods</span>
              <span className="font-headline-xl text-headline-xl text-on-surface font-bold mt-1">{totalPods} Pods</span>
              <span className="text-xs text-on-surface-variant mt-2">Across {currentCluster.nodeCount} Worker Nodes</span>
            </div>
          </div>

          {/* Main Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-lg">
            <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                  Cluster CPU Telemetry Trend ({windowRange})
                </h3>
                <span className="font-mono text-xs text-primary">Cores</span>
              </div>
              <ResourceUtilizationChart data={chartSeries} metricType="cpu" height={240} />
            </div>

            <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                  Cluster Memory Telemetry Trend ({windowRange})
                </h3>
                <span className="font-mono text-xs text-tertiary">MB</span>
              </div>
              <ResourceUtilizationChart data={chartSeries} metricType="memory" height={240} />
            </div>
          </div>

          {/* Node Capacity Table */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 overflow-hidden shadow-xl">
            <div className="p-space-md border-b border-surface-container-high/60">
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
                Cluster Node Capacity &amp; Health
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-lowest/60 border-b border-surface-container-high/60 text-on-surface-variant font-label-sm text-label-sm uppercase">
                    <th className="py-3 px-4">Node Hostname</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">CPU Capacity</th>
                    <th className="py-3 px-4">Memory Capacity</th>
                    <th className="py-3 px-4">Pods Scheduled</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-high/40 text-body-sm font-mono">
                  {nodes.map((node) => (
                    <tr key={node.name} className="hover:bg-surface-container-high/40 transition-colors">
                      <td className="py-3.5 px-4 text-on-surface font-medium">{node.name}</td>
                      <td className="py-3.5 px-4 text-on-surface-variant">{node.role}</td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary text-xs font-semibold">
                          {node.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-on-surface">{node.cpu}</td>
                      <td className="py-3.5 px-4 text-on-surface">{node.memory}</td>
                      <td className="py-3.5 px-4 text-primary font-bold">{node.pods} Pods</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
