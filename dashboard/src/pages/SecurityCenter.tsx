import React, { useState, useRef } from 'react';
import { ShieldAlert, ShieldCheck, AlertCircle, AlertTriangle, Info, ChevronDown, ChevronUp, RefreshCw, Upload } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Finding {
  title: string;
  message: string;
  severity: string;
  source?: string;
  rule_id?: string;
  line?: number;
  suggestion?: string;
}

const SeverityIcon = ({ s }: { s: string }) => {
  if (s === 'critical' || s === 'error') return <AlertCircle size={16} />;
  if (s === 'warning') return <AlertTriangle size={16} />;
  return <Info size={16} />;
};

const colors: Record<string, { bg: string; border: string; text: string }> = {
  critical: { bg: '#fee2e2', border: '#fca5a5', text: '#7f1d1d' }, // red-100, border, red-900
  error:    { bg: '#ffe4e6', border: '#fda4af', text: '#881337' }, // rose-100, border, rose-900
  warning:  { bg: '#fef3c7', border: '#fcd34d', text: '#78350f' }, // amber-100, border, amber-900
  info:     { bg: '#dbeafe', border: '#93c5fd', text: '#1e3a8a' }, // blue-100, border, blue-900
};
const darkColors: Record<string, string> = {
  critical: 'dark:bg-red-900 dark:border-red-700 dark:text-red-100',
  error:    'dark:bg-rose-900 dark:border-rose-700 dark:text-rose-100',
  warning:  'dark:bg-amber-900 dark:border-amber-700 dark:text-amber-100',
  info:     'dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100',
};

const FindingCard: React.FC<{ f: Finding }> = ({ f }) => {
  const [open, setOpen] = useState(false);
  const s = f.severity in colors ? f.severity : 'info';
  const c = colors[s];
  return (
    <div
      className={`rounded-xl border p-4 transition-all ${darkColors[s]}`}
      style={{ background: c.bg, borderColor: c.border, color: c.text }}
    >
      <div className="flex items-start gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <span className="mt-0.5 shrink-0"><SeverityIcon s={f.severity} /></span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-[14px]">{f.title}</span>
            <div className="flex items-center gap-2 shrink-0">
              {f.line && <span className="text-xs font-mono opacity-70">Line {f.line}</span>}
              <span className="opacity-60">{open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
            </div>
          </div>
          <p className={`text-sm mt-1 opacity-85 ${!open && 'line-clamp-1'}`}>{f.message}</p>
          {open && (
            <div className="mt-3 space-y-2">
              {f.suggestion && (
                <div className="p-3 rounded-lg bg-white/40 dark:bg-black/20 border border-inherit text-sm">
                  <span className="font-semibold block mb-1 opacity-75">💡 Suggestion</span>
                  {f.suggestion}
                </div>
              )}
              <div className="flex gap-3 text-xs font-mono opacity-60">
                {f.source && <span>Source: {f.source}</span>}
                {f.rule_id && <><span>•</span><span>Rule: {f.rule_id}</span></>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Static demo data shown when no backend scan done yet
const DEMO_FINDINGS: Finding[] = [
  { title: 'Hardcoded API key detected', message: 'A string that appears to be a high-entropy secret or API key is hardcoded in the source code.', severity: 'critical', source: 'bandit', rule_id: 'B105', line: 12, suggestion: "Use os.getenv('API_KEY') or a secrets manager instead." },
  { title: 'Use of insecure MD5 hash function', message: 'Use of weak MD5 hash for security-sensitive purposes.', severity: 'warning', source: 'bandit', rule_id: 'B303', line: 89, suggestion: 'Replace hashlib.md5() with hashlib.sha256().' },
  { title: 'SQL query constructed via string formatting', message: 'Possible SQL injection via string concatenation.', severity: 'error', source: 'bandit', rule_id: 'B608', line: 34, suggestion: 'Use parameterized queries or an ORM.' },
];

export const SecurityCenter: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>(DEMO_FINDINGS);
  const [loading, setLoading] = useState(false);
  const [isDemo, setIsDemo] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === 'py') setLanguage('python');
    else if (ext === 'java') setLanguage('java');
    else if (ext === 'cpp') setLanguage('cpp');
    const reader = new FileReader();
    reader.onload = (e) => {
      setCode(e.target?.result as string ?? '');
      setError(null);
    };
    reader.readAsText(file);
  };

  const runScan = async () => {
    if (!code.trim()) { setError('Please upload a file to scan first.'); return; }
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API}/analyze/full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, language: language, enable_custom_rules: true }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();
      const secFindings = data.findings?.filter((f: Finding) => f.source === 'bandit' || f.severity === 'critical' || f.severity === 'error') ?? [];
      setFindings(secFindings.length > 0 ? secFindings : []);
      setIsDemo(false);
    } catch (e: any) {
      setError('Backend not connected or failed — showing demo data.');
      setFindings(DEMO_FINDINGS);
      setIsDemo(true);
    } finally {
      setLoading(false);
    }
  };

  const critical = findings.filter(f => f.severity === 'critical' || f.severity === 'error').length;

  return (
    <div className="space-y-6 page-enter">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-1">Security Center</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Static Application Security Testing (SAST) — powered by Bandit.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input ref={fileRef} type="file" className="hidden" accept=".py,.java,.cpp"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
          <button onClick={() => fileRef.current?.click()} className="btn-ghost text-sm py-2 px-3 border border-[var(--border)] rounded-xl bg-white dark:bg-black font-semibold shadow-sm">
             <Upload size={14} className="inline mr-1" /> {code ? 'Change File' : 'Upload File'}
          </button>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm ${
            critical === 0
              ? 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100'
              : 'bg-red-100 text-red-900 dark:bg-red-900 dark:text-red-100'
          }`}>
            {critical === 0 ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
            {critical === 0 ? 'Secure' : `${critical} Critical Issues`}
          </div>
          <button onClick={runScan} disabled={loading} className="btn-primary text-sm py-2">
            {loading ? <><span className="spinner" /> Scanning...</> : <><RefreshCw size={14} /> Run Live Scan</>}
          </button>
        </div>
      </div>

      {isDemo && (
        <div className="rounded-xl p-4 text-sm font-medium flex items-center gap-2" style={{ background: 'var(--panel-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
          ℹ️ Showing demo data. Click "Run Live Scan" to analyze real code via the backend.
          {error && <span style={{ color: '#de638a' }}>{error}</span>}
        </div>
      )}

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Critical / Error', count: findings.filter(f => f.severity === 'critical' || f.severity === 'error').length, color: '#ef4444' },
          { label: 'Warnings', count: findings.filter(f => f.severity === 'warning').length, color: '#f59e0b' },
          { label: 'Info', count: findings.filter(f => f.severity === 'info').length, color: '#3b82f6' },
        ].map(stat => (
          <div key={stat.label} className="panel p-4 text-center">
            <p className="text-2xl font-bold" style={{ color: stat.color }}>{stat.count}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-bold">Vulnerability Report</h2>
        {findings.length === 0 ? (
          <div className="panel p-12 text-center">
            <ShieldCheck size={48} className="mx-auto mb-4 text-emerald-500" />
            <p className="font-semibold text-emerald-600 dark:text-emerald-400">No security vulnerabilities found.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {findings.map((f, i) => <FindingCard key={i} f={f} />)}
          </div>
        )}
      </div>
    </div>
  );
};
