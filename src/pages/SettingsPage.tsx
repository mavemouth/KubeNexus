import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const SettingsPage: React.FC = () => {
  const { settings, updateSettings } = useApp();

  const [safetyMarginPct, setSafetyMarginPct] = useState(settings.safetyMarginPct || 20);
  const [minObservationDays, setMinObservationDays] = useState(settings.minObservationDays || 7);
  const [prometheusUrl, setPrometheusUrl] = useState(settings.prometheusUrl || 'http://prometheus.monitoring.svc.cluster.local:9090');
  const [scrapeInterval, setScrapeInterval] = useState(settings.scrapeIntervalSeconds || 30);
  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl || 'http://localhost:8000/api/v1');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettings({
      safetyMarginPct,
      minObservationDays,
      prometheusUrl,
      scrapeIntervalSeconds: scrapeInterval,
      apiBaseUrl
    });
  };

  return (
    <div className="flex flex-col w-full space-y-space-lg pb-space-xl">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm px-2.5 py-0.5 rounded-full bg-primary-container/20 text-primary border border-primary-container/30 font-semibold">
              SYSTEM CONFIGURATION
            </span>
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight mt-1">
            Engine &amp; Integration Settings
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
            Configure safety margins, minimum telemetry observation windows, Prometheus scrapers, and API parameters.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-space-lg">
        {/* Safety Rules Panel */}
        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-surface-container-high">
            <span className="material-symbols-outlined text-[22px] text-tertiary">shield</span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
              Optimization Engine Safety Rules
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1">
                Peak Safety Headroom Margin (%)
              </label>
              <input
                type="number"
                value={safetyMarginPct}
                onChange={(e) => setSafetyMarginPct(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-md focus:outline-none focus:border-primary-container"
              />
              <span className="text-[11px] text-on-surface-variant mt-1 block">
                Additional percentage added on top of observed P99 peak usage for safety buffer.
              </span>
            </div>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1">
                Minimum Telemetry Observation Window (Days)
              </label>
              <input
                type="number"
                value={minObservationDays}
                onChange={(e) => setMinObservationDays(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-md focus:outline-none focus:border-primary-container"
              />
              <span className="text-[11px] text-on-surface-variant mt-1 block">
                Minimum required telemetry collection period before generating recommendations.
              </span>
            </div>
          </div>
        </div>

        {/* Telemetry Integration Panel */}
        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-surface-container-high">
            <span className="material-symbols-outlined text-[22px] text-primary">monitoring</span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
              Prometheus Telemetry Scraper Endpoint
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1">
                Prometheus Endpoint URL
              </label>
              <input
                type="url"
                value={prometheusUrl}
                onChange={(e) => setPrometheusUrl(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-md font-mono text-xs focus:outline-none focus:border-primary-container"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1">
                Metric Scrape Interval (Seconds)
              </label>
              <input
                type="number"
                value={scrapeInterval}
                onChange={(e) => setScrapeInterval(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-md focus:outline-none focus:border-primary-container"
              />
            </div>
          </div>
        </div>

        {/* FastAPI Backend URL */}
        <div className="p-space-lg rounded-xl bg-surface-container-low/80 backdrop-blur-xl border border-surface-container-high/60 shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-surface-container-high">
            <span className="material-symbols-outlined text-[22px] text-secondary">api</span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
              FastAPI Backend Endpoint Configuration
            </h2>
          </div>

          <div>
            <label className="block text-xs font-medium text-on-surface-variant mb-1">
              Backend Service URL (VITE_API_BASE_URL)
            </label>
            <input
              type="text"
              value={apiBaseUrl}
              onChange={(e) => setApiBaseUrl(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface-container border border-surface-container-highest text-on-surface text-body-md font-mono text-xs focus:outline-none focus:border-primary-container"
            />
            <span className="text-[11px] text-on-surface-variant mt-1 block">
              Direct connection endpoint to FastAPI Python optimization microservice.
            </span>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-headline-sm font-semibold hover:brightness-110 shadow-lg"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
