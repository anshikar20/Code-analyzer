import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  Bot, 
  Settings2, 
  LineChart,
  Code2,
  Zap
} from 'lucide-react';

const navItems = [
  { path: '/',            icon: LayoutDashboard, label: 'Overview' },
  { path: '/security',    icon: ShieldAlert,     label: 'Security Center' },
  { path: '/ai-review',   icon: Bot,             label: 'AI Review' },
  { path: '/rules',       icon: Settings2,       label: 'Rule Management' },
  { path: '/analytics',   icon: LineChart,       label: 'Analytics' },
  { path: '/doc-gen',     icon: Code2,           label: 'Doc Generator' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 h-screen fixed left-0 top-0 flex flex-col sidebar-gradient border-r border-[var(--border)]">
      {/* Logo */}
      <div className="p-6 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#de638a] to-[#4a3267] flex items-center justify-center shadow-lg shadow-purple-900/40">
            <Zap size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-white tracking-tight">CodePulse AI</h1>
            <p className="text-[10px] text-purple-300/70 uppercase tracking-widest font-medium">Enterprise Intelligence</p>
          </div>
        </div>
      </div>

      <div className="mx-4 my-2 h-px bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-[13.5px] font-medium relative ${
                isActive
                  ? 'bg-white/10 text-white nav-active-bar'
                  : 'text-purple-200/60 hover:bg-white/5 hover:text-purple-100'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon size={17} className={isActive ? 'text-[#de638a]' : ''} />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-purple-300/50 font-medium">v2.1.0 — All systems normal</span>
        </div>
      </div>
    </aside>
  );
};
