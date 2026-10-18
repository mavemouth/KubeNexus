import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useApp } from '../../context/AppContext';

export const Layout: React.FC = () => {
  const { toastMessage, setToastMessage } = useApp();

  return (
    <div className="min-h-screen bg-background text-on-surface font-body-md flex">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Container */}
      <div className="pl-60 flex-1 flex flex-col min-w-0">
        {/* Header Navigation Bar */}
        <Header />

        {/* Dynamic Page Content */}
        <main className="relative pt-16 w-full min-h-screen bg-surface px-space-lg py-space-md">
          <Outlet />
        </main>
      </div>

      {/* Global Toast Feedback Popup */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-container-high border border-primary-container/40 text-on-surface shadow-2xl backdrop-blur-xl animate-bounce">
          <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
          <span className="font-body-md text-body-md font-medium">{toastMessage}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="ml-2 text-on-surface-variant hover:text-on-surface"
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}
    </div>
  );
};
