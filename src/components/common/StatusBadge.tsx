import React from 'react';
import { ProvisioningStatus } from '../../types';

interface StatusBadgeProps {
  status: ProvisioningStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  let badgeStyle = 'bg-surface-container-high text-on-surface-variant border-surface-container-highest';
  let dotStyle = 'bg-on-surface-variant';
  let icon = 'info';

  switch (status) {
    case 'Healthy':
      badgeStyle = 'bg-tertiary-container/20 text-tertiary border-tertiary-container/40';
      dotStyle = 'bg-tertiary';
      icon = 'check_circle';
      break;
    case 'Over-provisioned':
      badgeStyle = 'bg-secondary-container/20 text-secondary border-secondary-container/40';
      dotStyle = 'bg-secondary';
      icon = 'trending_down';
      break;
    case 'Under-provisioned':
      badgeStyle = 'bg-error-container/30 text-error border-error-container/60';
      dotStyle = 'bg-error animate-pulse';
      icon = 'warning';
      break;
    case 'Warning':
      badgeStyle = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      dotStyle = 'bg-amber-400';
      icon = 'report_problem';
      break;
    case 'Critical':
      badgeStyle = 'bg-error-container/50 text-error border-error-container/80';
      dotStyle = 'bg-error animate-ping';
      icon = 'error';
      break;
  }

  const px = size === 'sm' ? 'px-2 py-0.5' : 'px-2.5 py-1';
  const text = size === 'sm' ? 'text-[11px]' : 'text-label-sm';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-label-sm ${px} ${text} ${badgeStyle}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dotStyle}`} />
      <span className="font-semibold tracking-wide">{status}</span>
    </span>
  );
};
