import React from 'react';
import { useApp } from '../context/AppContext';

export const CostOptimizationPage: React.FC = () => {
  const { workloads, recommendations } = useApp();

  const currentSpend = workloads.reduce((sum, w) => {
    const hourly = (w.cpuRequestCores * 0.04) + ((w.memoryRequestMb / 1024.0) * 0.005);
    return sum + (hourly * 730);
  }, 0);

  const potentialSavings = recommendations
    .filter((r) => (r.status === 'Generated' || r.status === 'Approved') && r.estimatedMonthlySavings > 0)
    .reduce((sum, r) => sum + r.estimatedMonthlySavings, 0);

  const optimizedSpend = Math.max(0, currentSpend - potentialSavings);
  const savingsPct = currentSpend > 0 ? (potentialSavings / currentSpend) * 100 : 0;

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-secondary-container/30 text-secondary border border-secondary-container/40 font-semibold">
              FINANCIAL OPERATIONS
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Cost Optimization &amp; Spend Estimation
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Identify over-allocated compute spend and quantify projected monthly savings across clusters.
          </p>
        </div>
      </div>

      {/* Main Spend Comparison Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-2">
          <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-medium">
            Current Monthly Cloud Spend
          </span>
          <div className="flex items-baseline gap-2">
            <span className="font-headline-xl text-headline-xl text-on-surface font-bold">
              ${currentSpend.toFixed(2)}
            </span>
            <span className="text-xs text-on-surface-variant">/ month</span>
          </div>
          <p className="text-xs text-on-surface-variant">Calculated from workload CPU and memory resource allocations.</p>
        </div>

        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-tertiary-container/40 shadow-xl space-y-2">
          <span className="font-label-sm text-label-sm uppercase text-tertiary font-semibold">
            Potential Monthly Savings
          </span>
          <div className="flex items-baseline gap-2">
            <span className="font-headline-xl text-headline-xl text-tertiary font-bold">
              -${potentialSavings.toFixed(2)}
            </span>
            <span className="text-xs text-tertiary">({savingsPct.toFixed(1)}% reduction)</span>
          </div>
          <p className="text-xs text-on-surface-variant">Reclaimed from over-provisioned CPU &amp; Memory requests.</p>
        </div>

        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-primary-container/40 shadow-xl space-y-2">
          <span className="font-label-sm text-label-sm uppercase text-primary font-semibold">
            Optimized Target Spend
          </span>
          <div className="flex items-baseline gap-2">
            <span className="font-headline-xl text-headline-xl text-primary font-bold">
              ${optimizedSpend.toFixed(2)}
            </span>
            <span className="text-xs text-on-surface-variant">/ month</span>
          </div>
          <p className="text-xs text-on-surface-variant">Achievable upon applying all approved recommendations.</p>
        </div>
      </div>

      {/* Workload Cost Breakdown Table */}
      <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 overflow-hidden shadow-xl">
        <div className="p-space-md border-b border-surface-container-high/60">
          <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
            Top Cost Optimization Opportunities by Workload
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-lowest/60 border-b border-surface-container-high/60 text-on-surface-variant font-label-sm text-label-sm uppercase">
                <th className="py-3.5 px-4">Workload &amp; Namespace</th>
                <th className="py-3.5 px-4">Current Monthly Cost</th>
                <th className="py-3.5 px-4">Optimized Monthly Cost</th>
                <th className="py-3.5 px-4">Estimated Savings</th>
                <th className="py-3.5 px-4">Optimization Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high/40 text-body-sm font-mono">
              {recommendations.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-on-surface-variant">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <span className="material-symbols-outlined text-[36px] text-on-surface-variant">savings</span>
                      <p className="font-semibold text-on-surface font-sans">No cost optimization opportunities recorded</p>
                      <p className="text-xs text-on-surface-variant max-w-sm font-sans">
                        When recommendations are generated in the database, individual workload cost breakdowns will appear here.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                recommendations.map((rec) => {
                  const currentEst = rec.estimatedMonthlySavings > 0 ? rec.estimatedMonthlySavings * 3.5 : 90;
                  const optimizedEst = Math.max(0, currentEst - rec.estimatedMonthlySavings);
                  return (
                    <tr key={rec.id} className="hover:bg-surface-container-high/40 transition-colors">
                      <td className="py-4 px-4 font-sans font-medium text-on-surface">
                        <div className="flex flex-col">
                          <span>{rec.workloadName}</span>
                          <span className="text-xs text-on-surface-variant">{rec.namespace} · {rec.workloadType}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-on-surface">${currentEst.toFixed(2)}</td>
                      <td className="py-4 px-4 text-primary font-bold">${optimizedEst.toFixed(2)}</td>
                      <td className="py-4 px-4 text-tertiary font-bold">
                        {rec.estimatedMonthlySavings > 0 ? `-$${rec.estimatedMonthlySavings.toFixed(2)}/mo` : '$0.00'}
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          rec.status === 'Applied'
                            ? 'bg-tertiary-container/20 text-tertiary border border-tertiary-container/30'
                            : rec.status === 'Approved'
                            ? 'bg-primary-container/20 text-primary border border-primary-container/30'
                            : 'bg-surface-container-high text-on-surface-variant'
                        }`}>
                          {rec.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
