import React from 'react';
import { RiskLevel, ConfidenceLevel } from '../../types';

export const RiskIndicator: React.FC<{ risk: RiskLevel }> = ({ risk }) => {
  let style = 'bg-tertiary-container/20 text-tertiary border-tertiary-container/30';
  if (risk === 'Medium') {
    style = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
  } else if (risk === 'High') {
    style = 'bg-error-container/30 text-error border-error-container/50';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border font-label-sm text-label-sm ${style}`}>
      <span className="material-symbols-outlined text-[13px]">shield</span>
      <span>{risk} Risk</span>
    </span>
  );
};

export const ConfidenceBadge: React.FC<{ confidence: ConfidenceLevel }> = ({ confidence }) => {
  let style = 'bg-tertiary-container/20 text-tertiary border-tertiary-container/30';
  if (confidence === 'Medium') {
    style = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
  } else if (confidence === 'Low') {
    style = 'bg-error-container/30 text-error border-error-container/50';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border font-label-sm text-label-sm ${style}`}>
      <span className="material-symbols-outlined text-[13px]">verified</span>
      <span>{confidence} Confidence</span>
    </span>
  );
};
