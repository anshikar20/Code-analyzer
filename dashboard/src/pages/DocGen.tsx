import React, { useState } from 'react';
import { FileText, Wand2, Copy, Check, Code2, RefreshCw } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const LANGUAGES = ['python', 'javascript', 'java', 'c', 'cpp'];

const SAMPLE = `def process_payment(amount, currency='USD', user_id=None):
    if amount <= 0:
        raise ValueError('Amount must be positive')
    # Payment processing logic here
    return {'status': 'success', 'transaction_id': 'txn_12345'}`;

export const DocGen: React.FC = () => {
  const [code, setCode] = useState(SAMPLE);
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [docstring, setDocstring] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    if (!code.trim()) return;
    setLoading(true); setError(null); setDocstring(null);
    try {
      const res = await fetch(`${API}/ai/docstring`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();
      setDocstring(data.content ?? '# No docstring generated.');
    } catch (e: any) {
      setError(e.message.includes('Failed to fetch')
        ? '❌ Cannot connect to backend. Make sure FastAPI server is running on port 8000.'
        : `❌ ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const copy = () => {
    if (docstring) {
      navigator.clipboard.writeText(docstring);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 page-enter">
      <div>
        <h1 className="text-3xl font-bold mb-1">Doc Generator</h1>
        <p className="text-slate-500 dark:text-slate-400">
          Automatically generate comprehensive docstrings from your code using Gemini AI.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Code input */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Code2 size={16} style={{ color: '#de638a' }} />
              Function / Class Code
            </h2>
            <div className="flex items-center gap-2">
              <select
                value={language}
                onChange={e => setLanguage(e.target.value)}
                className="input-field text-xs"
                style={{ width: 'auto', padding: '5px 10px' }}
              >
                {LANGUAGES.map(l => <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>)}
              </select>
              <button onClick={() => { setCode(SAMPLE); setDocstring(null); }} className="btn-ghost text-xs py-1.5 px-2">
                <RefreshCw size={12} />
              </button>
            </div>
          </div>

          <div className="panel overflow-hidden" style={{ background: '#0f0b1a', borderColor: '#2e2048' }}>
            <div className="flex items-center gap-1.5 px-4 py-2 border-b" style={{ borderColor: '#2e2048' }}>
              <span className="w-3 h-3 rounded-full bg-red-500/70" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
              <span className="w-3 h-3 rounded-full bg-green-500/70" />
              <span className="ml-2 text-xs font-mono" style={{ color: '#7a6a96' }}>function.py</span>
            </div>
            <textarea
              value={code}
              onChange={e => setCode(e.target.value)}
              className="w-full resize-none outline-none font-mono text-sm p-4"
              style={{ minHeight: '260px', background: 'transparent', color: '#e9d8ff', caretColor: '#de638a' }}
              spellCheck={false}
            />
          </div>

          {error && <p className="text-sm font-medium" style={{ color: '#de638a' }}>{error}</p>}

          <button
            onClick={generate}
            disabled={loading || !code.trim()}
            className="btn-primary w-full justify-center py-3 text-sm"
          >
            {loading ? <><span className="spinner" /> Generating...</> : <><Wand2 size={16} /> Generate Docstring</>}
          </button>
        </div>

        {/* Right: Docstring output */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold flex items-center gap-2">
              <FileText size={16} style={{ color: '#de638a' }} />
              Generated Docstring
            </h2>
            {docstring && (
              <button onClick={copy} className="btn-ghost text-xs py-1.5 px-3">
                {copied ? <><Check size={12} className="text-emerald-500" /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
            )}
          </div>

          <div className="panel overflow-hidden" style={{ background: '#0f0b1a', borderColor: '#2e2048', minHeight: '340px' }}>
            <div className="flex items-center gap-1.5 px-4 py-2 border-b" style={{ borderColor: '#2e2048' }}>
              <span className="w-3 h-3 rounded-full bg-red-500/70" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
              <span className="w-3 h-3 rounded-full bg-green-500/70" />
              <span className="ml-2 text-xs font-mono" style={{ color: '#7a6a96' }}>docstring_output.py</span>
            </div>

            {!docstring && !loading && (
              <div className="flex flex-col items-center justify-center h-64">
                <FileText size={40} className="mb-3 opacity-30" style={{ color: '#7a6a96' }} />
                <p className="text-sm" style={{ color: '#7a6a96' }}>Generated documentation will appear here</p>
              </div>
            )}
            {loading && (
              <div className="flex flex-col items-center justify-center h-64" style={{ color: '#de638a' }}>
                <Wand2 size={40} className="mb-3 animate-pulse" />
                <p className="text-sm font-semibold">Writing documentation<span className="cursor" /></p>
              </div>
            )}
            {docstring && !loading && (
              <pre className="p-4 text-sm font-mono overflow-x-auto whitespace-pre-wrap" style={{ color: '#e9d8ff' }}>
                {docstring}
              </pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
