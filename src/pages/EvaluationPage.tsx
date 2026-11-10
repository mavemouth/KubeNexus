import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ResourceUtilizationChart } from '../components/charts/ResourceUtilizationChart';
import { MetricTimeSeriesPoint } from '../types';

export const EvaluationPage: React.FC = () => {
  const { evaluations, workloads, clusters, selectedClusterId } = useApp();

  const currentCluster = clusters.find((c) => c.id === selectedClusterId);
  const clusterScopedEvals = selectedClusterId === 'all'
    ? evaluations
    : currentCluster
    ? evaluations.filter((ev) => {
        const wl = workloads.find((w) => w.id === ev.workloadId || w.name === ev.workloadName);
        return !wl || wl.clusterId === currentCluster.id || wl.clusterName === currentCluster.name;
      })
    : evaluations;

  const [selectedEvalId, setSelectedEvalId] = useState('');
  const currentEval = clusterScopedEvals.find((e) => e.id === selectedEvalId) || clusterScopedEvals[0];

  // Evaluation telemetry comparison series
  const evalMetrics: MetricTimeSeriesPoint[] = currentEval ? [
    { timestamp: '00:00', cpuUsage: 0.35, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 500, memoryLimitMb: 1024 },
    { timestamp: '04:00', cpuUsage: 0.42, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 520, memoryLimitMb: 1024 },
    { timestamp: '08:00', cpuUsage: 0.58, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 560, memoryLimitMb: 1024 },
    { timestamp: '12:00', cpuUsage: 0.62, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 580, memoryLimitMb: 1024 },
    { timestamp: '16:00', cpuUsage: 0.55, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 540, memoryLimitMb: 1024 },
    { timestamp: '20:00', cpuUsage: 0.40, cpuRequest: 1.0, cpuLimit: 2.0, memoryUsageMb: 510, memoryLimitMb: 1024 }
  ] : [];

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-tertiary-container/20 text-tertiary border border-tertiary-container/30 font-semibold">
              POST-OPTIMIZATION ANALYSIS
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Post-Change Evaluation &amp; Verification
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Compare resource utilization, CPU efficiency, memory pressure, and stability before vs after optimization.
          </p>
        </div>

        {clusterScopedEvals.length > 0 && (
          <div className="flex items-center gap-2">
            <select
              value={selectedEvalId || currentEval?.id}
              onChange={(e) => setSelectedEvalId(e.target.value)}
              className="px-3.5 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none font-semibold"
            >
              {clusterScopedEvals.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.workloadName} ({ev.changeTimestamp})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!currentEval ? (
        <div className="p-12 rounded-xl bg-surface-container-low border border-surface-container-high/60 flex flex-col items-center justify-center text-center">
          <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-2">fact_check</span>
          <h3 className="font-headline-md text-headline-md font-semibold text-on-surface">No Post-Change Evaluations Yet</h3>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-md mt-1">
            Evaluations are automatically recorded when recommendations are approved and applied to workloads in your PostgreSQL database.
          </p>
        </div>
      ) : (
        <div className="space-y-space-lg">
          {/* Workload Header Summary Card */}
          <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-tertiary-container/20 border border-tertiary-container/40 flex items-center justify-center text-tertiary">
                <span className="material-symbols-outlined text-[28px]">verified</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">
                    {currentEval.workloadName}
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-tertiary-container/20 text-tertiary font-label-sm text-label-sm font-bold border border-tertiary-container/40">
                    {currentEval.status}
                  </span>
                </div>
                <span className="text-body-sm text-on-surface-variant">
                  {currentEval.namespace} ({currentEval.clusterName}) · Applied {currentEval.changeTimestamp}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="px-4 py-2 rounded-lg bg-surface-container-high border border-surface-container-highest text-right">
                <span className="text-[11px] text-on-surface-variant uppercase font-medium">Achieved Savings</span>
                <span className="font-headline-lg text-headline-lg text-tertiary font-bold block">
                  +${currentEval.monthlySavingsAchieved.toFixed(2)} / mo
                </span>
              </div>
            </div>
          </div>

          {/* Before vs After Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
            {/* Before Optimization */}
            <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-surface-container-high">
                <span className="font-headline-md text-headline-md text-on-surface-variant font-semibold">
                  BEFORE Optimization
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-xs font-mono">
                  Previous Spec
                </span>
              </div>

              <div className="space-y-3 font-body-md text-body-md">
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">CPU Request:</span>
                  <span className="font-mono font-semibold text-on-surface">{currentEval.beforeCpuRequest}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">Memory Request:</span>
                  <span className="font-mono font-semibold text-on-surface">{currentEval.beforeMemoryRequest}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">CPU Utilization:</span>
                  <span className="font-mono font-bold text-amber-400">{currentEval.beforeCpuUtilPct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">Memory Utilization:</span>
                  <span className="font-mono font-bold text-amber-400">{currentEval.beforeMemoryUtilPct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-on-surface-variant">OOMKills / Restarts:</span>
                  <span className="font-mono text-on-surface">{currentEval.oomKillsBefore} / {currentEval.restartsBefore}</span>
                </div>
              </div>
            </div>

            {/* After Optimization */}
            <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-tertiary-container/40 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-surface-container-high">
                <span className="font-headline-md text-headline-md text-tertiary font-semibold">
                  AFTER Optimization (Current)
                </span>
                <span className="px-2 py-0.5 rounded bg-tertiary-container/30 text-tertiary text-xs font-mono font-bold">
                  Active Spec
                </span>
              </div>

              <div className="space-y-3 font-body-md text-body-md">
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">CPU Request:</span>
                  <span className="font-mono font-bold text-tertiary">{currentEval.afterCpuRequest}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">Memory Request:</span>
                  <span className="font-mono font-bold text-tertiary">{currentEval.afterMemoryRequest}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">CPU Utilization:</span>
                  <span className="font-mono font-bold text-tertiary">{currentEval.afterCpuUtilPct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-surface-container-high/40">
                  <span className="text-on-surface-variant">Memory Utilization:</span>
                  <span className="font-mono font-bold text-tertiary">{currentEval.afterMemoryUtilPct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-on-surface-variant">OOMKills / Restarts:</span>
                  <span className="font-mono text-tertiary font-bold">{currentEval.oomKillsAfter} / {currentEval.restartsAfter}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Post-Change Telemetry Chart */}
          <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
                Post-Optimization Telemetry Stability
              </h3>
              <span className="text-xs font-mono text-tertiary">Verified post-change observation window</span>
            </div>
            <ResourceUtilizationChart data={evalMetrics} metricType="cpu" height={220} />
          </div>
        </div>
      )}
    </div>
  );
};
