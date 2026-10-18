import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const AlertsPage: React.FC = () => {
  const { alerts, resolveAlert } = useApp();
  const [severityFilter, setSeverityFilter] = useState('all');

  const filteredAlerts = alerts.filter((a) => {
    return severityFilter === 'all' || a.severity === severityFilter;
  });

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-error-container/30 text-error border border-error-container/40 font-semibold">
              SYSTEM ALERTS &amp; EXCEPTIONS
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Operational Notification Center
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Monitored alerts for high utilization, OOMKills, stale telemetry, and recommendation expirations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-sm focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="Critical">Critical Only</option>
            <option value="Warning">Warning Only</option>
            <option value="Info">Info Only</option>
          </select>
        </div>
      </div>

      {/* Alerts Catalog */}
      <div className="space-y-space-md">
        {filteredAlerts.length === 0 ? (
          <div className="p-12 rounded-xl bg-surface-container-low border border-surface-container-high/60 flex flex-col items-center justify-center text-center">
            <span className="material-symbols-outlined text-[48px] text-tertiary mb-2">verified_user</span>
            <h3 className="font-headline-md text-headline-md font-semibold text-on-surface">No Active Alerts</h3>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-md mt-1">
              {alerts.length === 0
                ? 'All systems and workloads are healthy. No active exceptions or alerts in the database.'
                : 'No alerts match the selected severity filter.'}
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-space-md rounded-xl bg-surface-container-low/80 backdrop-blur-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg ${
              alert.severity === 'Critical' ? 'border-error-container/60' : 'border-surface-container-high/60'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`p-2.5 rounded-lg mt-0.5 ${alert.severity === 'Critical' ? 'bg-error-container/30 text-error' : 'bg-amber-500/15 text-amber-300'}`}>
                <span className="material-symbols-outlined text-[24px]">
                  {alert.severity === 'Critical' ? 'error' : 'warning'}
                </span>
              </div>

              <div className="flex flex-col space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                    {alert.title}
                  </h3>
                  <span className={`px-2 py-0.2 rounded text-[10px] font-bold uppercase ${
                    alert.severity === 'Critical' ? 'bg-error-container/40 text-error' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-on-surface-variant">· {alert.timestamp}</span>
                </div>
                <p className="text-body-sm text-on-surface-variant max-w-3xl">
                  {alert.description}
                </p>
                <div className="text-xs text-on-surface-variant font-mono">
                  Affected Workload: <strong className="text-on-surface">{alert.affectedWorkload}</strong> ({alert.clusterName})
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end md:self-auto">
              {alert.status === 'Active' ? (
                <button
                  onClick={() => resolveAlert(alert.id)}
                  className="px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-bright text-on-surface text-xs font-semibold border border-surface-container-highest transition-colors"
                >
                  Mark Resolved
                </button>
              ) : (
                <span className="text-xs text-tertiary font-medium flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  Resolved
                </span>
              )}
            </div>
          </div>
        )))}
      </div>
    </div>
  );
};
