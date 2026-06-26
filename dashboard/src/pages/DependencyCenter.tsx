import React from 'react';
import { Package, PackageX, ExternalLink, RefreshCw, ShieldCheck } from 'lucide-react';

interface Dep {
  name: string;
  version: string;
  status: 'vulnerable' | 'clean';
  cve?: string;
  description?: string;
  fixedIn?: string;
}

const DEPS: Dep[] = [
  {
    name: 'requests',
    version: '2.25.1',
    status: 'vulnerable',
    cve: 'CVE-2023-32289',
    description: 'Requests leaks the Proxy-Authorization header to the destination server when redirected to an HTTPS endpoint.',
    fixedIn: '2.31.0',
  },
  { name: 'fastapi',    version: '0.103.1', status: 'clean' },
  { name: 'pydantic',   version: '2.5.0',   status: 'clean' },
  { name: 'uvicorn',    version: '0.24.0',  status: 'clean' },
];

export const DependencyCenter: React.FC = () => {
  const vulnCount = DEPS.filter(d => d.status === 'vulnerable').length;

  return (
    <div className="space-y-6 page-enter">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-1">Dependency Center</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Software Composition Analysis (SCA) for your packages.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm ${
            vulnCount === 0
              ? 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100'
              : 'bg-red-100 text-red-900 dark:bg-red-900 dark:text-red-100'
          }`}>
            {vulnCount === 0 ? <ShieldCheck size={16} /> : <PackageX size={16} />}
            {vulnCount} {vulnCount === 1 ? 'Vulnerability' : 'Vulnerabilities'}
          </div>
          <button className="btn-ghost text-sm py-2">
            <RefreshCw size={14} /> Scan
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="panel p-4 text-center">
          <p className="text-2xl font-bold" style={{ color: '#ef4444' }}>{vulnCount}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Vulnerable</p>
        </div>
        <div className="panel p-4 text-center">
          <p className="text-2xl font-bold" style={{ color: '#10b981' }}>{DEPS.length - vulnCount}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Clean</p>
        </div>
        <div className="panel p-4 text-center">
          <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{DEPS.length}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Total Packages</p>
        </div>
      </div>

      {/* Package list */}
      <div className="panel overflow-hidden">
        <div className="px-6 py-4 border-b font-bold text-base" style={{ borderColor: 'var(--border)' }}>
          Package Report
        </div>
        <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
          {DEPS.map((dep) => (
            <div
              key={dep.name}
              className="p-5 flex flex-col md:flex-row gap-4 transition-colors"
              style={{ background: 'var(--panel)' }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--panel-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'var(--panel)')}
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  {dep.status === 'vulnerable'
                    ? <PackageX size={18} style={{ color: '#ef4444' }} />
                    : <Package size={18} style={{ color: '#10b981' }} />
                  }
                  <span className="font-bold text-[15px]" style={{ color: 'var(--text)' }}>{dep.name}</span>
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded font-bold"
                    style={{
                      background: dep.status === 'vulnerable' ? '#fee2e2' : 'var(--panel-2)',
                      color: dep.status === 'vulnerable' ? '#7f1d1d' : 'var(--text)',
                    }}
                  >
                    {dep.version}
                  </span>
                  {dep.cve && (
                    <span className="badge badge-critical">{dep.cve}</span>
                  )}
                </div>

                {dep.description && (
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    {dep.description}
                  </p>
                )}

                {dep.fixedIn && (
                  <div className="flex items-center gap-3 text-sm font-mono">
                    <span style={{ color: 'var(--text-muted)' }}>
                      Fixed in: <span className="font-bold" style={{ color: '#10b981' }}>{dep.fixedIn}</span>
                    </span>
                    <a
                      href="#"
                      className="flex items-center gap-1 font-semibold"
                      style={{ color: '#6d3d8e' }}
                      onClick={e => e.preventDefault()}
                    >
                      Advisory <ExternalLink size={12} />
                    </a>
                  </div>
                )}
              </div>

              <div className="shrink-0 flex items-center">
                {dep.status === 'vulnerable' ? (
                  <button
                    className="btn-accent text-sm py-2 px-4"
                    onClick={() => alert(`Auto-fix for ${dep.name} would run: pip install ${dep.name}>=${dep.fixedIn}`)}
                  >
                    Auto-Fix
                  </button>
                ) : (
                  <span className="text-sm font-bold" style={{ color: '#10b981' }}>✓ Clean</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
