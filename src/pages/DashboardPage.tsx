import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { workloads, recommendations, alerts, refreshData } = useApp();

  const activeRecommendations = recommendations.filter((r) => r.status === 'Generated' || r.status === 'Approved');

  // Dynamically calculated from live database records
  const totalSpend = workloads.reduce((sum, w) => {
    const hourly = (w.cpuRequestCores * 0.04) + ((w.memoryRequestMb / 1024.0) * 0.005);
    return sum + (hourly * 730);
  }, 0);

  const potentialSavings = activeRecommendations
    .filter((r) => r.estimatedMonthlySavings > 0)
    .reduce((sum, r) => sum + r.estimatedMonthlySavings, 0);

  const savingsPct = totalSpend > 0 ? (potentialSavings / totalSpend) * 100 : 0;

  const totalCpuUsed = workloads.reduce((sum, w) => sum + w.cpuUsageCores, 0);
  const totalCpuReq = workloads.reduce((sum, w) => sum + w.cpuRequestCores, 0);
  const cpuEfficiency = totalCpuReq > 0 ? (totalCpuUsed / totalCpuReq) * 100 : 0;

  const totalMemUsedMb = workloads.reduce((sum, w) => sum + (w.memoryRequestMb * (w.memoryUtilizationPct / 100)), 0);
  const totalMemReqMb = workloads.reduce((sum, w) => sum + w.memoryRequestMb, 0);
  const memEfficiency = totalMemReqMb > 0 ? (totalMemUsedMb / totalMemReqMb) * 100 : 0;

  return (
    <div className="flex flex-col w-full space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e2d42]">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Cluster Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {workloads.length > 0
              ? `Live telemetry across ${workloads.length} monitored workloads · Connected to PostgreSQL`
              : 'Live PostgreSQL database connected · Connect a Kubernetes cluster or register workloads to start analysis'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/clusters')}
            className="px-3.5 py-2 rounded-lg bg-[#1a273a] hover:bg-[#22324b] text-slate-200 text-sm font-medium border border-[#263750] transition-colors flex items-center gap-2"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-slate-400">hub</span>
            <span>Manage Clusters</span>
          </button>
          <button
            onClick={async () => {
              await refreshData();
              alert('Telemetry synchronized with database.');
            }}
            className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-colors shadow-md flex items-center gap-2"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">sync</span>
            <span>Sync Live State</span>
          </button>
        </div>
      </div>

      {/* Clean 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="p-5 rounded-xl bg-[#142032] border border-[#22334c] flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Monthly Cloud Spend
            </span>
            <span className="material-symbols-outlined text-sky-400 text-[20px]">payments</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100">${totalSpend.toFixed(2)}</div>
            <div className="text-xs text-emerald-400 font-medium mt-1">
              {potentialSavings > 0
                ? `-$${potentialSavings.toFixed(2)} / mo (${savingsPct.toFixed(1)}%) potential savings`
                : '$0.00 potential savings identified'}
            </div>
          </div>
        </div>

        {/* Card 2 */}
        <div className="p-5 rounded-xl bg-[#142032] border border-[#22334c] flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              CPU Efficiency
            </span>
            <span className="material-symbols-outlined text-sky-400 text-[20px]">memory</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100">{cpuEfficiency.toFixed(1)}%</div>
            <div className="text-xs text-slate-400 mt-1">
              {totalCpuUsed.toFixed(1)} Cores used / {totalCpuReq.toFixed(1)} Cores requested
            </div>
          </div>
        </div>

        {/* Card 3 */}
        <div className="p-5 rounded-xl bg-[#142032] border border-[#22334c] flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Memory Efficiency
            </span>
            <span className="material-symbols-outlined text-emerald-400 text-[20px]">hard_drive</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-slate-100">{memEfficiency.toFixed(1)}%</div>
            <div className="text-xs text-slate-400 mt-1">
              {(totalMemUsedMb / 1024.0).toFixed(1)} GB used / {(totalMemReqMb / 1024.0).toFixed(1)} GB requested
            </div>
          </div>
        </div>

        {/* Card 4 */}
        <div
          onClick={() => navigate('/recommendations')}
          className="p-5 rounded-xl bg-[#142032] border border-[#22334c] hover:border-sky-500/50 transition-colors flex flex-col justify-between cursor-pointer"
        >
          <div className="flex items-start justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Active Recommendations
            </span>
            <span className="material-symbols-outlined text-sky-400 text-[20px]">auto_awesome</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-sky-400">{activeRecommendations.length}</div>
            <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <span>Review Optimizations</span>
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations & Alerts Main Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table (2 cols) */}
        <div className="lg:col-span-2 rounded-xl bg-[#142032] border border-[#22334c] p-5">
          <div className="flex items-center justify-between pb-4 border-b border-[#1e2d42]">
            <h2 className="text-base font-semibold text-slate-100">
              High-Impact Recommendations
            </h2>
            <button
              onClick={() => navigate('/recommendations')}
              className="text-xs text-sky-400 hover:underline font-medium"
            >
              View All ({recommendations.length})
            </button>
          </div>

          <div className="overflow-x-auto mt-2">
            {recommendations.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <span className="material-symbols-outlined text-slate-500 text-[36px] mb-2">auto_awesome</span>
                <p className="text-sm font-medium text-slate-300">No active recommendations in database</p>
                <p className="text-xs text-slate-500 max-w-sm mt-1">
                  Once workloads are connected and analyzed, AI-driven right-sizing recommendations will appear here.
                </p>
                <button
                  onClick={() => navigate('/clusters')}
                  className="mt-4 px-3.5 py-1.5 rounded-lg bg-sky-500/20 text-sky-400 hover:bg-sky-500/30 text-xs font-semibold border border-sky-500/40 transition-colors"
                >
                  Register Cluster
                </button>
              </div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-slate-400 text-xs uppercase border-b border-[#1e2d42]">
                    <th className="py-3 px-2">Workload</th>
                    <th className="py-3 px-2">CPU Specs</th>
                    <th className="py-3 px-2">Mem Specs</th>
                    <th className="py-3 px-2">Savings</th>
                    <th className="py-3 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2d42]">
                  {recommendations.slice(0, 4).map((rec) => (
                    <tr key={rec.id} className="hover:bg-[#1a273a] transition-colors">
                      <td className="py-3 px-2 font-medium text-slate-200">
                        <div>{rec.workloadName}</div>
                        <div className="text-xs text-slate-400 font-normal">{rec.namespace}</div>
                      </td>
                      <td className="py-3 px-2 text-xs font-mono">
                        <span className="text-slate-400">{rec.currentCpuRequest}</span>
                        <span className="text-sky-400 font-bold ml-1.5">→ {rec.recommendedCpuRequest}</span>
                      </td>
                      <td className="py-3 px-2 text-xs font-mono">
                        <span className="text-slate-400">{rec.currentMemoryRequest}</span>
                        <span className="text-emerald-400 font-bold ml-1.5">→ {rec.recommendedMemoryRequest}</span>
                      </td>
                      <td className="py-3 px-2 text-xs font-semibold text-emerald-400">
                        {rec.estimatedMonthlySavings >= 0 ? `+$${rec.estimatedMonthlySavings.toFixed(2)}/mo` : `-$${Math.abs(rec.estimatedMonthlySavings).toFixed(2)}/mo`}
                      </td>
                      <td className="py-3 px-2 text-right">
                        <button
                          onClick={() => navigate(`/recommendations/${rec.id}`)}
                          className="px-3 py-1 rounded bg-[#1e2d42] hover:bg-[#283b54] text-slate-200 text-xs font-medium transition-colors"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Active Alerts Widget (1 col) */}
        <div className="rounded-xl bg-[#142032] border border-[#22334c] p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-[#1e2d42]">
              <h2 className="text-base font-semibold text-slate-100">
                Active System Alerts
              </h2>
              <button onClick={() => navigate('/alerts')} className="text-xs text-sky-400 hover:underline font-medium">
                View Alerts
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {alerts.length === 0 ? (
                <div className="py-10 flex flex-col items-center justify-center text-center">
                  <span className="material-symbols-outlined text-emerald-400 text-[32px] mb-2">check_circle</span>
                  <p className="text-sm font-medium text-slate-200">System Healthy</p>
                  <p className="text-xs text-slate-400 mt-1">No active resource pressure or saturation alerts</p>
                </div>
              ) : (
                alerts.slice(0, 3).map((a) => (
                  <div key={a.id} className="p-3 rounded-lg bg-[#1a273a] border border-[#263750] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-200">{a.title}</span>
                      <span className="text-[10px] text-slate-400">{a.timestamp}</span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2">
                      {a.description}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
