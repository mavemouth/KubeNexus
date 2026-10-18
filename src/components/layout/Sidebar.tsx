import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useApp } from '../../context/AppContext';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { alerts, clusters, selectedClusterId } = useApp();

  const activeAlertsCount = alerts.filter((a) => a.status === 'Active').length;
  const currentCluster = clusters.find((c) => c.id === selectedClusterId) || clusters[0];

  const navItems = [
    { name: 'Overview', path: '/overview', icon: 'dashboard' },
    { name: 'Clusters', path: '/clusters', icon: 'dns' },
    { name: 'Workloads', path: '/workloads', icon: 'deployed_code' },
    { name: 'Monitoring', path: '/monitoring', icon: 'monitoring' },
    { name: 'Recommendations', path: '/recommendations', icon: 'auto_awesome' },
    { name: 'Cost Optimization', path: '/cost-optimization', icon: 'attach_money' },
    { name: 'Alerts', path: '/alerts', icon: 'notifications_active', badge: activeAlertsCount },
    { name: 'Changes & Audit', path: '/changes-audit', icon: 'history' },
    { name: 'Evaluation', path: '/evaluation', icon: 'analytics' },
    { name: 'Settings', path: '/settings', icon: 'settings' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-[#111c2d] border-r border-[#1e2d42] z-50 flex flex-col justify-between">
      <div className="flex flex-col flex-1 min-h-0">
        {/* Brand Logo */}
        <div className="h-16 px-5 flex items-center gap-3 border-b border-[#1e2d42]">
          <div className="w-8 h-8 rounded-lg bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <span className="material-symbols-outlined text-[20px]">hub</span>
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-slate-100 text-base tracking-tight leading-none">
              KubeNexus
            </span>
            <span className="text-xs text-slate-400 leading-none mt-1">
              K8s Optimizer
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path === '/overview' && location.pathname === '/') ||
              (location.pathname.startsWith('/workloads') && item.path === '/workloads') ||
              (location.pathname.startsWith('/recommendations') && item.path === '/recommendations');

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 font-medium border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a273a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-[19px]">
                    {item.icon}
                  </span>
                  <span>{item.name}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-medium border border-rose-500/30">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Cluster Status Footer */}
      <div className="p-4 border-t border-[#1e2d42] bg-[#0d1624]">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 min-w-0">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-slate-300 truncate font-medium">
              {currentCluster ? currentCluster.name : 'k8s-prod'}
            </span>
          </div>
          <span className="text-emerald-400 text-[11px]">Online</span>
        </div>
      </div>
    </aside>
  );
};
