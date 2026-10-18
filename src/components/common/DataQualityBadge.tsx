import React from 'react';
import { DataQualityStatus } from '../../types';

export const DataQualityBadge: React.FC<{ status: DataQualityStatus }> = ({ status }) => {
  switch (status) {
    case 'valid':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-tertiary-container/15 text-tertiary font-label-sm text-label-sm border border-tertiary-container/30">
          <span className="material-symbols-outlined text-[13px]">check_circle</span>
          <span>Verified Telemetry</span>
        </span>
      );
    case 'insufficient_evidence':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 font-label-sm text-label-sm border border-amber-500/30">
          <span className="material-symbols-outlined text-[13px]">history_toggle_off</span>
          <span>Insufficient Evidence</span>
        </span>
      );
    case 'stale_data':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-error-container/20 text-error font-label-sm text-label-sm border border-error-container/40">
          <span className="material-symbols-outlined text-[13px]">update_disabled</span>
          <span>Stale Telemetry (&gt;48h)</span>
        </span>
      );
    case 'monitoring_unavailable':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm border border-surface-container-highest">
          <span className="material-symbols-outlined text-[13px]">cloud_off</span>
          <span>Prometheus Down</span>
        </span>
      );
    default:
      return null;
  }
};
