import React, { useState, useRef } from 'react';
import { Upload, Zap, ShieldCheck, AlertTriangle, AlertCircle, Info, RotateCcw, FileCode } from 'lucide-react';
import { Editor } from '@monaco-editor/react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const LANGUAGES = ['python', 'java', 'cpp'];

interface Finding {
  title: string;
  message: string;
  severity: string;
  source?: string;
  rule_id?: string;
  line?: number;
  suggestion?: string;
}

interface AnalysisResult {
  status: string;
  findings: Finding[];
  summary: Record<string, number>;
  scores?: { health: number; security: number; quality: number; maintainability: number };
}

const severityIcon = (s: string) => {
  switch (s) {
    case 'critical':
    case 'error':   return <AlertCircle size={17} />;
    case 'warning': return <AlertTriangle size={17} />;
    default:        return <Info size={17} />;
  }
};

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 border-red-300 text-red-900',
  error:    'bg-rose-100 border-rose-300 text-rose-900',
  warning:  'bg-amber-100 border-amber-300 text-amber-900',
  info:     'bg-blue-100 border-blue-300 text-blue-900',
};
const severityColorsDark: Record<string, string> = {
  critical: 'dark:bg-red-900 dark:border-red-700 dark:text-red-100',
  error:    'dark:bg-rose-900 dark:border-rose-700 dark:text-rose-100',
  warning:  'dark:bg-amber-900 dark:border-amber-700 dark:text-amber-100',
  info:     'dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100',
};

const ScoreRing: React.FC<{ title: string; score: number; subtitle: string }> = ({ title, score, subtitle }) => {
  const color = score >= 90 ? '#10b981' : score >= 70 ? '#f59e0b' : '#ef4444';
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="panel p-3 flex flex-row items-center gap-4 transition-all h-full justify-between shadow-sm">
      <div className="flex flex-col">
        <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>{title}</p>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>
      </div>
      <div className="relative w-12 h-12 shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" stroke="var(--border)" strokeWidth="8" />
          <circle
            cx="40" cy="40" r="36" fill="none"
            stroke={color} strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold" style={{ color }}>
          {score}
        </span>
      </div>
    </div>
  );
};

export const Overview: React.FC = () => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  
  const fileRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);

  const scores = result?.scores ?? { health: 0, security: 0, quality: 0, maintainability: 0 };

  const handleFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === 'py') setLanguage('python');
    else if (ext === 'java') setLanguage('java');
    else if (ext === 'cpp') setLanguage('cpp');
    const reader = new FileReader();
    reader.onload = (e) => setCode(e.target?.result as string ?? '');
    reader.readAsText(file);
  };

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const highlightLine = (line: number) => {
    if (!editorRef.current) return;
    editorRef.current.revealLineInCenter(line);
    const oldDecorations = decorationsRef.current;
    const newDecorations = editorRef.current.deltaDecorations(oldDecorations, [
      {
        range: new ((window as any).monaco).Range(line, 1, line, 1),
        options: { isWholeLine: true, className: 'bg-red-500/20 dark:bg-red-500/40' }
      }
    ]);
    decorationsRef.current = newDecorations;
  };

  const analyze = async () => {
    if (!code.trim()) { setError('Please provide code first.'); return; }
    setLoading(true); setError(null); setResult(null);
    if (decorationsRef.current.length && editorRef.current) {
        decorationsRef.current = editorRef.current.deltaDecorations(decorationsRef.current, []);
    }
    try {
      const res = await fetch(`${API}/analyze/full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, enable_custom_rules: true }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data: AnalysisResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message.includes('Failed to fetch')
        ? '❌ Cannot connect to backend. Make sure the FastAPI server is running on port 8000.'
        : e.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setCode(''); setResult(null); setError(null); };

  const filtered = result?.findings.filter(f =>
    filter === 'all' ? true : f.severity === filter
  ) ?? [];

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-4 page-enter">
      {/* Top Toolbar */}
      <div className="panel p-4 flex items-center justify-between shadow-sm shrink-0">
        <div className="flex items-center gap-4">
          <button className="btn-ghost flex items-center gap-2 px-3 py-2" onClick={() => fileRef.current?.click()}>
            <Upload size={18} /> Upload File
          </button>
          <input ref={fileRef} type="file" className="hidden" accept=".py,.java,.cpp"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="input-field max-w-[150px]"
          >
            {LANGUAGES.map(l => <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-4">
          {error && <span className="text-red-700 font-bold dark:text-red-400 text-sm">{error}</span>}
          {result && (
            <button onClick={reset} className="btn-ghost text-sm py-2 px-3">
              <RotateCcw size={14} /> Clear
            </button>
          )}
          <button onClick={analyze} disabled={loading} className="btn-primary py-2 px-6">
            {loading ? <><span className="spinner" /> Analyzing...</> : <><Zap size={18} /> Analyze Code</>}
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Editor (Left side) */}
        <div className="flex-1 panel overflow-hidden shadow-sm border border-[var(--border)] relative flex flex-col">
          <div className="bg-[var(--panel-2)] px-4 py-2 text-sm font-mono border-b border-[var(--border)] font-bold text-[var(--text-muted)] flex items-center gap-2 shrink-0">
             <FileCode size={16} /> Code Editor
          </div>
          <div className="flex-1 min-h-0">
              <Editor
                height="100%"
                language={language}
                theme="vs-dark"
                value={code}
                onChange={value => setCode(value || '')}
                onMount={handleEditorDidMount}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    smoothScrolling: true,
                    padding: { top: 16 }
                }}
              />
          </div>
        </div>

        {/* Findings & Analysis (Right side) */}
        <div className="w-[450px] shrink-0 flex flex-col gap-4 overflow-hidden">
          {result ? (
            <>
              {/* Scores Grid */}
              <div className="flex gap-3 shrink-0">
                <div className="flex-1"><ScoreRing title="Quality"   score={scores.quality}         subtitle="Code Health" /></div>
                <div className="flex-1"><ScoreRing title="Security"  score={scores.security}        subtitle="Vulnerabilities" /></div>
              </div>

              {/* Findings Panel */}
              <div className="panel flex-1 flex flex-col overflow-hidden shadow-sm">
                <div className="p-4 border-b border-[var(--border)] shrink-0 space-y-3">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold">Findings <span className="text-[var(--text-muted)] font-normal text-sm">({result.findings.length})</span></h2>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {['all', 'critical', 'error', 'warning', 'info'].map(f => (
                      <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`text-xs font-bold uppercase tracking-wide px-3 py-1 rounded-full border transition-all ${
                          filter === f
                            ? 'border-[#6d3d8e] bg-[#6d3d8e] text-white'
                            : 'border-[var(--border)] hover:border-[var(--border-strong)] text-[var(--text-muted)]'
                        }`}
                      >
                        {f} {f !== 'all' && result.summary?.[f] !== undefined && `(${result.summary[f]})`}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {filtered.length === 0 ? (
                    <div className="text-center py-12">
                      <ShieldCheck size={48} className="mx-auto mb-4 text-emerald-500" />
                      <p className="font-bold text-emerald-700 dark:text-emerald-400">
                        {filter === 'all' ? 'No issues found! Clean code.' : `No ${filter} issues.`}
                      </p>
                    </div>
                  ) : (
                    filtered.map((f, i) => (
                      <IssueRow key={i} f={f} onLocate={() => f.line && highlightLine(f.line)} />
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="panel flex-1 flex items-center justify-center p-8 text-center shadow-sm">
               <div>
                  <Zap size={48} className="mx-auto mb-4 opacity-20" style={{ color: 'var(--text)' }} />
                  <p className="text-[var(--text-muted)] font-bold text-lg mb-2">Ready to Analyze</p>
                  <p className="text-sm text-[var(--text-faint)]">Paste code or upload a file and click analyze to see detailed metrics and findings here.</p>
               </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const IssueRow: React.FC<{ f: Finding, onLocate: () => void }> = ({ f, onLocate }) => {
  const [open, setOpen] = useState(false);
  const s = f.severity in severityColors ? f.severity : 'info';
  return (
    <div className={`rounded-lg border p-3 transition-all ${severityColors[s]} ${severityColorsDark[s]}`}>
      <div className="flex items-start gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <span className="mt-0.5 shrink-0 opacity-80">{severityIcon(f.severity)}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-bold text-sm leading-tight">{f.title}</span>
            <div className="flex items-center gap-2 shrink-0">
              {f.line && (
                <button 
                  onClick={(e) => { e.stopPropagation(); onLocate(); }}
                  className="text-xs font-mono px-2 py-0.5 rounded bg-black/10 dark:bg-white/10 hover:bg-black/20 dark:hover:bg-white/20 transition-colors"
                >
                  L{f.line}
                </button>
              )}
            </div>
          </div>
          <p className={`text-sm mt-1.5 opacity-90 leading-snug ${!open && 'line-clamp-2'}`}>{f.message}</p>
          {open && f.suggestion && (
            <div className="mt-3 p-2.5 rounded bg-black/5 dark:bg-black/20 border border-black/10 dark:border-white/10 text-sm">
              <span className="font-bold opacity-80 block mb-1">💡 Suggestion</span>
              {f.suggestion}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
