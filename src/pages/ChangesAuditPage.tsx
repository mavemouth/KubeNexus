import React from 'react';
import { useApp } from '../context/AppContext';

export const ChangesAuditPage: React.FC = () => {
  const { auditEvents } = useApp();

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-primary-container/20 text-primary border border-primary-container/30 font-semibold">
              INFRASTRUCTURE AUDIT TRAIL
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Changes &amp; Audit Trail
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Immutable log of all resource specification modifications, approvals, applications, and rollbacks.
          </p>
        </div>
      </div>

      {/* Audit Log DataTable */}
      <div className="rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-lowest/60 border-b border-surface-container-high/60 text-on-surface-variant font-label-sm text-label-sm uppercase">
                <th className="py-3.5 px-4">Timestamp &amp; User</th>
                <th className="py-3.5 px-4">Target Workload</th>
                <th className="py-3.5 px-4">Specification Transition</th>
                <th className="py-3.5 px-4">Action</th>
                <th className="py-3.5 px-4">Recommendation Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high/40 text-body-sm">
              {auditEvents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-on-surface-variant">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <span className="material-symbols-outlined text-[36px] text-on-surface-variant">history_edu</span>
                      <p className="font-semibold text-on-surface">No audit events recorded</p>
                      <p className="text-xs text-on-surface-variant max-w-sm">
                        All configuration approvals, rejections, and applied optimizations are immutably logged here.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                auditEvents.map((event) => (
                <tr key={event.id} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span className="font-semibold text-on-surface">{event.changedBy}</span>
                      <span className="text-xs text-on-surface-variant">{event.userRole} · {event.timestamp}</span>
                    </div>
                  </td>

                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span className="font-medium text-on-surface">{event.workloadName}</span>
                      <span className="text-xs text-on-surface-variant">{event.namespace} ({event.clusterName})</span>
                    </div>
                  </td>

                  <td className="py-4 px-4 font-mono text-xs">
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-on-surface-variant">CPU:</span>
                        <span className="line-through text-on-surface-variant">{event.previousCpuRequest}</span>
                        <span className="material-symbols-outlined text-[12px] text-primary">east</span>
                        <span className="text-primary font-bold">{event.newCpuRequest}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-on-surface-variant">Mem:</span>
                        <span className="line-through text-on-surface-variant">{event.previousMemoryRequest}</span>
                        <span className="material-symbols-outlined text-[12px] text-tertiary">east</span>
                        <span className="text-tertiary font-bold">{event.newMemoryRequest}</span>
                      </div>
                    </div>
                  </td>

                  <td className="py-4 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      event.action === 'Applied' ? 'bg-primary-container/20 text-primary border border-primary-container/40' :
                      event.action === 'Approved' ? 'bg-tertiary-container/20 text-tertiary border border-tertiary-container/40' :
                      'bg-surface-container-high text-on-surface-variant'
                    }`}>
                      {event.action}
                    </span>
                  </td>

                  <td className="py-4 px-4 font-mono text-xs">
                    <span className="text-primary hover:underline cursor-pointer">
                      {event.recommendationId}
                    </span>
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
