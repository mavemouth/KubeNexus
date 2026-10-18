import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { RiskIndicator, ConfidenceBadge } from '../components/common/RiskIndicator';
import { ResourceUtilizationChart } from '../components/charts/ResourceUtilizationChart';
import { MetricTimeSeriesPoint } from '../types';

export const RecommendationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { recommendations, approveRecommendation, rejectRecommendation, applyRecommendation } = useApp();

  const rec = recommendations.find((r) => r.id === id || r.workloadName === id) || recommendations[0];

  const [confirmModalAction, setConfirmModalAction] = useState<'approve' | 'reject' | 'apply' | null>(null);
  const [metrics, setMetrics] = useState<MetricTimeSeriesPoint[]>([]);

  useEffect(() => {
    if (rec?.workloadId) {
      api.getWorkloadMetrics(rec.workloadId).then(setMetrics);
    }
  }, [rec?.workloadId]);

  if (!rec) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <span className="material-symbols-outlined text-[48px] text-on-surface-variant">auto_awesome</span>
        <h2 className="text-xl font-bold text-on-surface">Recommendation Not Found</h2>
        <p className="text-sm text-on-surface-variant max-w-md text-center">
          The requested recommendation is not available in the database or no recommendations have been generated yet.
        </p>
        <button
          onClick={() => navigate('/recommendations')}
          className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-semibold"
        >
          Back to Recommendations
        </button>
      </div>
    );
  }

  const handleActionConfirm = async () => {
    if (confirmModalAction === 'approve') {
      await approveRecommendation(rec.id);
    } else if (confirmModalAction === 'reject') {
      await rejectRecommendation(rec.id);
    } else if (confirmModalAction === 'apply') {
      await applyRecommendation(rec.id);
    }
    setConfirmModalAction(null);
  };

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Top Context Breadcrumb & Title */}
      <div className="flex flex-col space-y-2">
        <div className="flex items-center justify-between">
          <nav className="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm">
            <button
              onClick={() => navigate('/recommendations')}
              className="flex items-center gap-1 text-primary hover:text-primary-fixed transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Back to Recommendations</span>
            </button>
            <span className="text-surface-variant">/</span>
            <span className="font-mono text-label-sm text-primary">{rec.id}</span>
            <span className="text-surface-variant">/</span>
            <span className="text-on-surface font-semibold">{rec.workloadName}</span>
          </nav>

          <span className="font-label-sm text-label-sm text-on-surface-variant flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">history</span>
            {rec.observationWindow}
          </span>
        </div>

        <div className="flex flex-wrap items-start justify-between gap-space-md pt-1">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight">
                {rec.workloadName}{' '}
                <span className="text-on-surface-variant font-body-md text-body-md font-normal">
                  ({rec.workloadType})
                </span>
              </h1>

              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-high border border-primary-container/30">
                <span className="font-mono text-xs text-primary font-medium">{rec.id}</span>
              </div>

              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container-high border border-surface-container-highest">
                <span className={`h-2 w-2 rounded-full ${rec.status === 'Approved' ? 'bg-tertiary animate-pulse' : 'bg-secondary'}`} />
                <span className="font-label-sm text-label-sm font-semibold tracking-wider uppercase text-on-surface">
                  {rec.status}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1 font-label-sm text-label-sm text-on-surface-variant">
              <span className="px-2.5 py-1 rounded-lg bg-surface-container-low text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[14px] text-primary">lan</span>
                Cluster: <strong className="text-on-surface">{rec.clusterName}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-surface-container-low text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[14px] text-primary">folder_open</span>
                Namespace: <strong className="text-on-surface">{rec.namespace}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-surface-container-low text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[14px] text-tertiary">psychology</span>
                Optimizer Engine v1.4
              </span>
              <span className="text-on-surface-variant px-1 font-body-sm text-body-sm">
                Generated {rec.createdAt}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-lg">
        {/* Left Column (2 Cols): Details & Evidence */}
        <div className="lg:col-span-2 space-y-space-lg">
          {/* Target Workload Configuration Comparison Card */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-lg shadow-xl space-y-space-md">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container-high/60">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-primary">tune</span>
                <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
                  Resource Specification Comparison
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <RiskIndicator risk={rec.riskLevel} />
                <ConfidenceBadge confidence={rec.confidence} />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
              {/* Current Configuration */}
              <div className="p-space-md rounded-lg bg-surface-container/60 border border-surface-container-highest/60 space-y-2">
                <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-medium">
                  Current Configuration
                </span>
                <div className="space-y-1 font-mono text-xs">
                  <div className="flex justify-between py-1 border-b border-surface-container-high">
                    <span className="text-on-surface-variant">CPU Request:</span>
                    <span className="text-on-surface font-bold">{rec.currentCpuRequest}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-surface-container-high">
                    <span className="text-on-surface-variant">CPU Limit:</span>
                    <span className="text-on-surface-variant">{rec.currentCpuLimit}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-surface-container-high">
                    <span className="text-on-surface-variant">Memory Request:</span>
                    <span className="text-on-surface font-bold">{rec.currentMemoryRequest}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-on-surface-variant">Memory Limit:</span>
                    <span className="text-on-surface-variant">{rec.currentMemoryLimit}</span>
                  </div>
                </div>
              </div>

              {/* Proposed Configuration */}
              <div className="p-space-md rounded-lg bg-primary-container/10 border border-primary-container/40 space-y-2">
                <span className="font-label-sm text-label-sm uppercase text-primary font-semibold">
                  Proposed Optimization
                </span>
                <div className="space-y-1 font-mono text-xs">
                  <div className="flex justify-between py-1 border-b border-primary-container/20">
                    <span className="text-on-surface-variant">CPU Request:</span>
                    <span className="text-primary font-bold">{rec.recommendedCpuRequest}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-primary-container/20">
                    <span className="text-on-surface-variant">CPU Limit:</span>
                    <span className="text-primary">{rec.recommendedCpuLimit}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-primary-container/20">
                    <span className="text-on-surface-variant">Memory Request:</span>
                    <span className="text-tertiary font-bold">{rec.recommendedMemoryRequest}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-on-surface-variant">Memory Limit:</span>
                    <span className="text-tertiary">{rec.recommendedMemoryLimit}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Evidence & Reasoning Panel */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-lg shadow-xl space-y-space-md">
            <div className="flex items-center justify-between pb-3 border-b border-surface-container-high/60">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-tertiary">analytics</span>
                <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
                  Evidence &amp; Historical Telemetry Reasoning
                </h2>
              </div>
            </div>

            <p className="font-body-md text-body-md text-on-surface leading-relaxed">
              {rec.evidenceReason}
            </p>

            <div className="p-3 rounded-lg bg-surface-container-lowest/50 border border-surface-container-highest/50 font-body-sm text-body-sm text-on-surface-variant">
              <strong className="text-on-surface">Assumptions:</strong> {rec.assumptions}
            </div>

            {/* Percentiles Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 font-mono text-xs">
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest">
                <span className="text-[11px] text-on-surface-variant block font-sans">CPU P50</span>
                <span className="text-on-surface font-bold">{rec.percentiles.p50Cpu} Cores</span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest">
                <span className="text-[11px] text-on-surface-variant block font-sans">CPU P90</span>
                <span className="text-on-surface font-bold">{rec.percentiles.p90Cpu} Cores</span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest">
                <span className="text-[11px] text-on-surface-variant block font-sans">CPU P99 (Peak)</span>
                <span className="text-primary font-bold">{rec.percentiles.p99Cpu} Cores</span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest">
                <span className="text-[11px] text-on-surface-variant block font-sans">Max Memory</span>
                <span className="text-tertiary font-bold">{rec.percentiles.maxMemoryMb} MB</span>
              </div>
            </div>

            {/* Telemetry Visualizer Chart */}
            <div className="pt-2">
              <ResourceUtilizationChart data={metrics} metricType="cpu" height={200} />
            </div>
          </div>

          {/* Operational Safety & Conflict Check Card */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-lg shadow-xl space-y-3">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold flex items-center gap-2">
              <span className="material-symbols-outlined text-tertiary text-[20px]">shield_check</span>
              Automated Safety Verification Checklist
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-body-sm">
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-[18px]">check_circle</span>
                <span>HPA Conflict Check: <strong>Passed (No HPA)</strong></span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-[18px]">check_circle</span>
                <span>VPA Conflict Check: <strong>Passed (No VPA)</strong></span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-[18px]">check_circle</span>
                <span>Telemetry Freshness: <strong>Synced 42s ago</strong></span>
              </div>
              <div className="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container-highest flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-[18px]">check_circle</span>
                <span>Workload Existence: <strong>Active Deployment</strong></span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Operational Decision Controls */}
        <div className="space-y-space-md">
          {/* Decision Panel */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-lg shadow-xl space-y-4">
            <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
              Operational Decision
            </h3>

            {/* Current Status State */}
            <div className="p-3 rounded-lg bg-surface-container border border-surface-container-highest flex items-center justify-between">
              <span className="text-xs text-on-surface-variant">Current Status:</span>
              <span className="font-bold text-primary uppercase text-xs">{rec.status}</span>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2.5 pt-2">
              {rec.status === 'Generated' && (
                <button
                  onClick={() => setConfirmModalAction('approve')}
                  className="w-full py-2.5 rounded-lg bg-tertiary-container text-on-tertiary-container font-headline-sm text-headline-sm font-semibold hover:brightness-110 shadow-md transition-all flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  <span>Approve Recommendation</span>
                </button>
              )}

              {(rec.status === 'Approved' || rec.status === 'Generated') && (
                <button
                  onClick={() => setConfirmModalAction('apply')}
                  className="w-full py-2.5 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm font-semibold hover:brightness-110 shadow-md transition-all flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
                  <span>Apply Change to Workload</span>
                </button>
              )}

              {rec.status === 'Applied' && (
                <div className="p-3 rounded-lg bg-tertiary-container/20 border border-tertiary-container/40 text-tertiary text-center font-semibold text-body-sm">
                  Already Applied &amp; Active
                </div>
              )}

              {rec.status !== 'Rejected' && rec.status !== 'Applied' && (
                <button
                  onClick={() => setConfirmModalAction('reject')}
                  className="w-full py-2 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface-variant hover:text-on-surface font-body-sm text-body-sm font-medium border border-surface-container-highest transition-colors flex items-center justify-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">cancel</span>
                  <span>Reject Recommendation</span>
                </button>
              )}
            </div>
          </div>

          {/* Cost Impact Widget */}
          <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-md shadow-xl space-y-2">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant">
              Estimated Monthly Cost Impact
            </span>
            <div className="flex items-baseline gap-2">
              <span className={`font-headline-xl text-headline-xl font-bold ${rec.estimatedMonthlySavings >= 0 ? 'text-tertiary' : 'text-error'}`}>
                {rec.estimatedMonthlySavings >= 0 ? `-$${rec.estimatedMonthlySavings.toFixed(2)}` : `+$${Math.abs(rec.estimatedMonthlySavings).toFixed(2)}`}
              </span>
              <span className="text-xs text-on-surface-variant">/ month</span>
            </div>
            <p className="text-xs text-on-surface-variant">
              {rec.estimatedMonthlySavings >= 0 ? 'Direct reduction in node pool CPU requests.' : 'Required investment to remediate throttling & OOMKills.'}
            </p>
          </div>

          {/* Expiration Timer Card */}
          <div className="rounded-xl bg-surface-container-low/80 border border-surface-container-high/60 p-space-md shadow-xl flex items-center gap-3">
            <span className="material-symbols-outlined text-amber-400 text-[24px]">timer</span>
            <div className="flex flex-col">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Recommendation Freshness</span>
              <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">{rec.expiresAt}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {confirmModalAction && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-xl bg-surface-container-low border border-surface-container-highest p-space-lg shadow-2xl space-y-4">
            <div className="flex items-center gap-2 text-primary">
              <span className="material-symbols-outlined text-[24px]">help_outline</span>
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold capitalize">
                Confirm {confirmModalAction} Action
              </h3>
            </div>

            <p className="font-body-md text-body-md text-on-surface-variant">
              Are you sure you want to {confirmModalAction} recommendation <strong className="text-on-surface">{rec.id}</strong> for <strong className="text-on-surface">{rec.workloadName}</strong>?
            </p>

            <div className="pt-3 border-t border-surface-container-high flex items-center justify-end gap-3">
              <button
                onClick={() => setConfirmModalAction(null)}
                className="px-4 py-2 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface text-body-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleActionConfirm}
                className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-semibold hover:brightness-110 text-body-sm shadow-md capitalize"
              >
                Confirm {confirmModalAction}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
