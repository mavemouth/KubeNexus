import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { ResourceUtilizationChart } from '../components/charts/ResourceUtilizationChart';
import { StatusBadge } from '../components/common/StatusBadge';
import { DataQualityBadge } from '../components/common/DataQualityBadge';
import { MetricTimeSeriesPoint } from '../types';

export const WorkloadDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { workloads, recommendations, runAnalysis } = useApp();

  const [timeRange, setTimeRange] = useState('24h');
  const [metrics, setMetrics] = useState<MetricTimeSeriesPoint[]>([]);

  const workload = workloads.find((w) => w.id === id || w.name === id) || workloads[0];
  const relatedRec = workload ? recommendations.find((r) => r.workloadId === workload.id || r.workloadName === workload.name) : undefined;

  useEffect(() => {
    if (workload?.id) {
      api.getWorkloadMetrics(workload.id, timeRange).then(setMetrics);
    }
  }, [workload?.id, timeRange]);

  if (!workload) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <span className="material-symbols-outlined text-[48px] text-on-surface-variant">layers_clear</span>
        <h2 className="text-xl font-bold text-on-surface">Workload Not Found</h2>
        <p className="text-sm text-on-surface-variant max-w-md text-center">
          The requested workload is not available in the PostgreSQL database or no workloads have been registered yet.
        </p>
        <button
          onClick={() => navigate('/workloads')}
          className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-semibold"
        >
          Back to Workloads
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Breadcrumb & Header */}
      <div className="flex flex-col space-y-2">
        <nav className="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm">
          <button
            onClick={() => navigate('/workloads')}
            className="flex items-center gap-1 text-primary hover:text-primary-fixed transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">arrow_back</span>
            <span>Back to Workloads</span>
          </button>
          <span className="text-surface-variant">/</span>
          <span className="text-on-surface-variant">{workload.namespace}</span>
          <span className="text-surface-variant">/</span>
          <span className="text-on-surface font-semibold">{workload.name}</span>
        </nav>

        <div className="flex flex-wrap items-start justify-between gap-4 pt-1">
          <div className="flex flex-col">
            <div className="flex items-center gap-3">
              <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight">
                {workload.name}
              </h1>
              <span className="font-body-md text-body-md text-on-surface-variant">
                ({workload.type})
              </span>
              <StatusBadge status={workload.status} />
              <DataQualityBadge status={workload.dataQualityStatus} />
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-2 font-label-sm text-label-sm text-on-surface-variant">
              <span>Cluster: <strong className="text-on-surface">{workload.clusterName}</strong></span>
              <span>·</span>
              <span>Namespace: <strong className="text-on-surface">{workload.namespace}</strong></span>
              <span>·</span>
              <span>Desired Replicas: <strong className="text-on-surface">{workload.replicasDesired}</strong></span>
              <span>·</span>
              <span>Analysis Window: <strong className="text-tertiary">14-Day P99 Profile</strong></span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => runAnalysis(workload.id)}
              className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm font-semibold hover:brightness-110 shadow-md flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">auto_fix_high</span>
              <span>Run Re-Analysis</span>
            </button>
          </div>
        </div>
      </div>

      {/* Active Recommendation Banner (if present) */}
      {relatedRec && (
        <div className="p-space-md rounded-xl bg-surface-container-low border border-primary-container/40 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-primary-container/20 text-primary mt-0.5">
              <span className="material-symbols-outlined text-[24px]">auto_awesome</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-headline-md text-headline-md text-on-surface font-semibold">
                  Optimization Recommendation Available
                </span>
                <span className="font-label-sm text-label-sm px-2 py-0.5 rounded bg-primary-container/20 text-primary font-bold">
                  {relatedRec.id}
                </span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5 max-w-2xl">
                {relatedRec.evidenceReason}
              </p>
            </div>
          </div>

          <button
            onClick={() => navigate(`/recommendations/${relatedRec.id}`)}
            className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm font-semibold hover:brightness-110 shadow-md whitespace-nowrap self-start md:self-auto"
          >
            Review Recommendation
          </button>
        </div>
      )}

      {/* Current Resource Specs & Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
        {/* CPU Config */}
        <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-medium">
              CPU Allocation
            </span>
            <span className="material-symbols-outlined text-primary text-[20px]">memory</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">Request:</span>
              <span className="font-mono font-semibold text-on-surface">{workload.cpuRequest}</span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">Limit:</span>
              <span className="font-mono text-on-surface-variant">{workload.cpuLimit}</span>
            </div>
            <div className="flex items-baseline justify-between pt-1 border-t border-surface-container-high">
              <span className="text-xs text-on-surface-variant">Current Usage:</span>
              <span className="font-mono text-primary font-bold">{workload.cpuUsageCores.toFixed(2)} Cores</span>
            </div>
          </div>
        </div>

        {/* Memory Config */}
        <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-medium">
              Memory Allocation
            </span>
            <span className="material-symbols-outlined text-tertiary text-[20px]">hard_drive</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">Request:</span>
              <span className="font-mono font-semibold text-on-surface">{workload.memoryRequestMb} MB</span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">Limit:</span>
              <span className="font-mono text-on-surface-variant">{workload.memoryLimitMb} MB</span>
            </div>
            <div className="flex items-baseline justify-between pt-1 border-t border-surface-container-high">
              <span className="text-xs text-on-surface-variant">Utilization:</span>
              <span className="font-mono text-tertiary font-bold">{workload.memoryUtilizationPct.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Stability & Pod Health */}
        <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-medium">
              Pod Stability Metrics
            </span>
            <span className="material-symbols-outlined text-amber-400 text-[20px]">healing</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">Pod Restarts:</span>
              <span className={`font-mono font-bold ${workload.restarts > 0 ? 'text-amber-400' : 'text-on-surface'}`}>
                {workload.restarts}
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-on-surface-variant">OOMKills (24h):</span>
              <span className={`font-mono font-bold ${workload.oomKills > 0 ? 'text-error' : 'text-on-surface'}`}>
                {workload.oomKills}
              </span>
            </div>
            <div className="flex items-baseline justify-between pt-1 border-t border-surface-container-high">
              <span className="text-xs text-on-surface-variant">CPU Throttling:</span>
              <span className={`font-mono font-bold ${workload.throttlingCount > 0 ? 'text-error' : 'text-tertiary'}`}>
                {workload.throttlingCount} events
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Telemetry Charts */}
      <div className="space-y-space-md">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
            Historical Resource Telemetry
          </h2>
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-surface-container-low border border-surface-container-highest">
            {['1h', '6h', '24h', '7d'].map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors ${
                  timeRange === r
                    ? 'bg-primary-container text-on-primary-container font-bold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-lg">
          {/* CPU Chart */}
          <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                CPU Utilization vs Request &amp; Limit
              </span>
              <span className="text-xs font-mono text-primary">Cores</span>
            </div>
            <ResourceUtilizationChart data={metrics} metricType="cpu" height={220} />
          </div>

          {/* Memory Chart */}
          <div className="p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                Memory Usage vs Limit
              </span>
              <span className="text-xs font-mono text-tertiary">MB</span>
            </div>
            <ResourceUtilizationChart data={metrics} metricType="memory" height={220} />
          </div>
        </div>
      </div>
    </div>
  );
};
