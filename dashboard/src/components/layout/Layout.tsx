import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Moon, Sun } from 'lucide-react';

export const Layout: React.FC = () => {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('omni-theme');
    if (stored) return stored === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('omni-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('omni-theme', 'light');
    }
  }, [isDark]);

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <Sidebar />
      
      <main className="ml-64 min-h-screen flex flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-end px-8 py-3 border-b"
          style={{ background: 'var(--panel)', borderColor: 'var(--border)' }}>
          <button
            onClick={() => setIsDark(!isDark)}
            className="w-9 h-9 rounded-xl flex items-center justify-center transition-all"
            style={{ background: 'var(--panel-2)', border: '1px solid var(--border)' }}
            title="Toggle theme"
          >
            {isDark
              ? <Sun size={16} className="text-yellow-400" />
              : <Moon size={16} style={{ color: 'var(--text-muted)' }} />
            }
          </button>
        </header>

        <div className="flex-1 p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
