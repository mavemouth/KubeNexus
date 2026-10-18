import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { RiskIndicator, ConfidenceBadge } from '../components/common/RiskIndicator';

export const RecommendationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { recommendations, approveRecommendation, applyRecommendation } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');

  const filteredRecs = recommendations.filter((r) => {
    const matchesSearch =
      r.workloadName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.namespace.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    const matchesRisk = riskFilter === 'all' || r.riskLevel === riskFilter;

    return matchesSearch && matchesStatus && matchesRisk;
  });

  const totalMonthlySavings = recommendations.reduce(
    (acc, r) => acc + (r.estimatedMonthlySavings > 0 ? r.estimatedMonthlySavings : 0),
    0
  );
  const pendingCount = recommendations.filter((r) => r.status === 'Generated' || r.status === 'Reviewed').length;
  const approvedCount = recommendations.filter((r) => r.status === 'Approved').length;

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-primary-container/20 text-primary border border-primary-container/30 font-semibold">
              OPTIMIZATION ENGINE
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Explainable Resource Recommendations
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Algorithmic right-sizing recommendations based on 14-day P99 utilization profiles and safety margins.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 rounded-lg bg-surface-container-high border border-surface-container-highest flex flex-col text-right">
            <span className="text-[11px] text-on-surface-variant uppercase font-medium">Potential Monthly Savings</span>
            <span className="font-headline-lg text-headline-lg text-tertiary font-bold tracking-tight">
              ${totalMonthlySavings.toFixed(2)} / mo
            </span>
          </div>
        </div>
      </div>

      {/* KPI Metric Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-space-md">
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Total Recommendations</span>
          <span className="font-headline-xl text-headline-xl text-on-surface font-bold mt-1">{recommendations.length}</span>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Pending Review</span>
          <span className="font-headline-xl text-headline-xl text-secondary font-bold mt-1">{pendingCount}</span>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Approved &amp; Ready</span>
          <span className="font-headline-xl text-headline-xl text-tertiary font-bold mt-1">{approvedCount}</span>
        </div>
        <div className="p-space-md rounded-xl bg-surface-container-low/70 border border-surface-container-high/50 flex flex-col justify-between">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">Engine Safety Profile</span>
          <span className="font-headline-xl text-headline-xl text-primary font-bold mt-1">20% Headroom</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-space-md p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-md">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[220px]">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-on-surface-variant">
              search
            </span>
            <input
              type="text"
              placeholder="Search by Recommendation ID, Workload, or Namespace..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface placeholder-on-surface-variant text-body-sm focus:outline-none focus:border-primary-container"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none focus:border-primary-container"
          >
            <option value="all">All Recommendation Statuses</option>
            <option value="Generated">Generated (Pending Review)</option>
            <option value="Approved">Approved</option>
            <option value="Applied">Applied</option>
            <option value="Rejected">Rejected</option>
            <option value="Expired">Expired</option>
          </select>

          {/* Risk Level Filter */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none focus:border-primary-container"
          >
            <option value="all">All Risk Profiles</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
          </select>
        </div>

        <div className="text-xs text-on-surface-variant font-mono">
          Showing <strong>{filteredRecs.length}</strong> Recommendations
        </div>
      </div>

      {/* Recommendation Cards Catalog */}
      <div className="grid grid-cols-1 gap-space-md">
        {filteredRecs.length === 0 ? (
          <div className="p-12 rounded-xl bg-surface-container-low border border-surface-container-high/60 flex flex-col items-center justify-center text-center">
            <span className="material-symbols-outlined text-[48px] text-on-surface-variant mb-2">auto_awesome</span>
            <h3 className="font-headline-md text-headline-md font-semibold text-on-surface">No Recommendations Found</h3>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-md mt-1">
              {recommendations.length === 0
                ? 'No recommendations exist in database yet. Connect a cluster or run analysis on workloads to generate right-sizing suggestions.'
                : 'No recommendations matched your active search or filter criteria.'}
            </p>
          </div>
        ) : (
          filteredRecs.map((rec) => (
          <div
            key={rec.id}
            className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 p-space-md shadow-lg flex flex-col lg:flex-row lg:items-center justify-between gap-space-md hover:bg-surface-container-high/40 transition-all"
          >
            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center gap-3">
                <span
                  onClick={() => navigate(`/recommendations/${rec.id}`)}
                  className="font-headline-md text-headline-md text-on-surface font-semibold hover:text-primary cursor-pointer transition-colors"
                >
                  {rec.workloadName}
                </span>
                <span className="font-mono text-xs text-primary font-medium px-2 py-0.5 rounded bg-primary-container/15 border border-primary-container/30">
                  {rec.id}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  rec.status === 'Approved' ? 'bg-tertiary-container/20 text-tertiary border border-tertiary-container/40' :
                  rec.status === 'Applied' ? 'bg-primary-container/20 text-primary border border-primary-container/40' :
                  rec.status === 'Rejected' ? 'bg-surface-container-high text-on-surface-variant' :
                  rec.status === 'Expired' ? 'bg-error-container/30 text-error' :
                  'bg-secondary-container/20 text-secondary border border-secondary-container/40'
                }`}>
                  {rec.status}
                </span>
                <RiskIndicator risk={rec.riskLevel} />
                <ConfidenceBadge confidence={rec.confidence} />
              </div>

              <p className="text-body-sm text-on-surface-variant line-clamp-2 max-w-3xl">
                {rec.evidenceReason}
              </p>

              {/* Spec Comparison Bar */}
              <div className="flex flex-wrap items-center gap-6 pt-1 font-mono text-xs">
                <div className="flex items-center gap-2 bg-surface-container/60 px-3 py-1.5 rounded-lg border border-surface-container-highest/40">
                  <span className="text-on-surface-variant font-sans">CPU Request:</span>
                  <span className="line-through text-on-surface-variant">{rec.currentCpuRequest}</span>
                  <span className="material-symbols-outlined text-[14px] text-primary">east</span>
                  <span className="text-primary font-bold">{rec.recommendedCpuRequest}</span>
                </div>

                <div className="flex items-center gap-2 bg-surface-container/60 px-3 py-1.5 rounded-lg border border-surface-container-highest/40">
                  <span className="text-on-surface-variant font-sans">Memory Request:</span>
                  <span className="line-through text-on-surface-variant">{rec.currentMemoryRequest}</span>
                  <span className="material-symbols-outlined text-[14px] text-tertiary">east</span>
                  <span className="text-tertiary font-bold">{rec.recommendedMemoryRequest}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-on-surface-variant font-sans">Estimated Cost Impact:</span>
                  <span className={`font-bold ${rec.estimatedMonthlySavings >= 0 ? 'text-tertiary' : 'text-error'}`}>
                    {rec.estimatedMonthlySavings >= 0 ? `-$${rec.estimatedMonthlySavings.toFixed(2)}/mo savings` : `+$${Math.abs(rec.estimatedMonthlySavings).toFixed(2)}/mo scale-up`}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-2 lg:flex-col lg:items-end justify-end">
              <button
                onClick={() => navigate(`/recommendations/${rec.id}`)}
                className="px-4 py-2 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface text-body-sm font-semibold border border-surface-container-highest transition-colors shadow-sm"
              >
                Inspect &amp; Review
              </button>

              {rec.status === 'Generated' && (
                <button
                  onClick={() => approveRecommendation(rec.id)}
                  className="px-4 py-2 rounded-lg bg-tertiary-container/30 text-tertiary hover:bg-tertiary-container/50 border border-tertiary-container/50 text-body-sm font-semibold transition-colors"
                >
                  Approve Change
                </button>
              )}

              {rec.status === 'Approved' && (
                <button
                  onClick={() => applyRecommendation(rec.id)}
                  className="px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-semibold hover:brightness-110 text-body-sm shadow-md transition-all"
                >
                  Apply Change
                </button>
              )}
            </div>
          </div>
        )))}
      </div>
    </div>
  );
};
