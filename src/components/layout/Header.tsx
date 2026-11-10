import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';

export const Header: React.FC = () => {
  const {
    clusters,
    selectedClusterId,
    setSelectedClusterId,
    selectedTimeRange,
    setSelectedTimeRange,
    alerts
  } = useApp();

  const [clusterDropdownOpen, setClusterDropdownOpen] = useState(false);
  const [timeDropdownOpen, setTimeDropdownOpen] = useState(false);

  const isAllClusters = selectedClusterId === 'all';
  const currentCluster = clusters.find((c) => c.id === selectedClusterId) || (isAllClusters ? null : clusters[0]);
  const activeAlertsCount = alerts.filter((a) => a.status === 'Active').length;
  const displayName = isAllClusters ? 'All Clusters (Fleet View)' : (currentCluster ? currentCluster.name : 'Select Cluster');

  const timeRanges = ['Last 1 Hour', 'Last 6 Hours', 'Last 24 Hours', 'Last 7 Days'];

  return (
    <header className="fixed top-0 left-60 right-0 h-16 bg-[#111c2d] border-b border-[#1e2d42] z-40 px-6 flex items-center justify-between">
      {/* Cluster & Time selectors */}
      <div className="flex items-center gap-3">
        {/* Cluster Dropdown */}
        <div className="relative">
          <button
            onClick={() => setClusterDropdownOpen(!clusterDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1a273a] hover:bg-[#22324b] text-slate-200 text-sm font-medium border border-[#263750] transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-sky-400">
              {isAllClusters ? 'public' : 'hub'}
            </span>
            <span>{displayName}</span>
            <span className="material-symbols-outlined text-[16px] text-slate-400">keyboard_arrow_down</span>
          </button>

          {clusterDropdownOpen && (
            <div className="absolute top-11 left-0 w-64 rounded-lg bg-[#142032] border border-[#24354d] shadow-xl p-2 z-50">
              <div className="px-2 py-1 text-[11px] font-medium text-slate-400 uppercase">
                Active Clusters
              </div>
              <button
                onClick={() => {
                  setSelectedClusterId('all');
                  setClusterDropdownOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left text-xs transition-colors mb-1 border-b border-[#1e2d42] pb-2 ${
                  selectedClusterId === 'all'
                    ? 'bg-sky-500/15 text-sky-400 font-medium'
                    : 'text-slate-300 hover:bg-[#1e2d42]'
                }`}
              >
                <div className="flex flex-col">
                  <span className="font-semibold">All Clusters (Fleet View)</span>
                  <span className="text-[10px] text-slate-400">{clusters.length} total clusters</span>
                </div>
                <span className="material-symbols-outlined text-[16px] text-sky-400">public</span>
              </button>
              {clusters.map((c) => (
                <button
                  key={c.id}
                  onClick={() => {
                    setSelectedClusterId(c.id);
                    setClusterDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left text-xs transition-colors ${
                    c.id === selectedClusterId
                      ? 'bg-sky-500/15 text-sky-400 font-medium'
                      : 'text-slate-300 hover:bg-[#1e2d42]'
                  }`}
                >
                  <div className="flex flex-col">
                    <span>{c.name}</span>
                    <span className="text-[10px] text-slate-400">{c.provider} · {c.workloadCount} workloads</span>
                  </div>
                  <span className={`h-2 w-2 rounded-full ${c.connectionStatus === 'Connected' ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Time Range Dropdown */}
        <div className="relative">
          <button
            onClick={() => setTimeDropdownOpen(!timeDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1a273a] hover:bg-[#22324b] text-slate-300 text-sm border border-[#263750] transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-[16px] text-slate-400">schedule</span>
            <span>{selectedTimeRange}</span>
            <span className="material-symbols-outlined text-[16px] text-slate-400">expand_more</span>
          </button>

          {timeDropdownOpen && (
            <div className="absolute top-11 left-0 w-40 rounded-lg bg-[#142032] border border-[#24354d] shadow-xl p-1.5 z-50">
              {timeRanges.map((tr) => (
                <button
                  key={tr}
                  onClick={() => {
                    setSelectedTimeRange(tr);
                    setTimeDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 rounded-md text-xs transition-colors ${
                    tr === selectedTimeRange
                      ? 'bg-sky-500/15 text-sky-400 font-medium'
                      : 'text-slate-300 hover:bg-[#1e2d42]'
                  }`}
                >
                  {tr}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Sync Status */}
        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <span>Synced 2s ago</span>
        </div>

        {/* Notifications Icon */}
        <button
          aria-label="Notifications"
          className="relative p-2 rounded-lg bg-[#1a273a] hover:bg-[#22324b] text-slate-300 transition-colors border border-[#263750]"
          type="button"
        >
          <span className="material-symbols-outlined text-[19px]">notifications</span>
          {activeAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-white font-semibold text-[10px]">
              {activeAlertsCount}
            </span>
          )}
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-2.5 pl-2">
          <div className="flex flex-col text-right leading-none">
            <span className="text-sm text-slate-200 font-medium">Alex M.</span>
            <span className="text-[11px] text-slate-400 mt-0.5">DevOps Lead</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-sky-500 text-slate-950 flex items-center justify-center font-bold text-xs">
            AM
          </div>
        </div>
      </div>
    </header>
  );
};
