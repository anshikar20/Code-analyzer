import React, { useState, useRef, useEffect } from 'react';
import { Bot, Sparkles, Send, Code2, RefreshCw } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const LANGUAGES = ['python', 'javascript', 'java', 'c', 'cpp'];

const SAMPLE_CODE = `def calculate_total(items):
    total = 0
    for i in items:
        total += i['price'] * i['quantity']
    return total`;

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// Simple markdown-to-html renderer
const renderMd = (md: string) =>
  md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/### (.*)/g, '<h3 class="text-base font-bold mt-4 mb-2" style="color:var(--text)">$1</h3>')
    .replace(/## (.*)/g,  '<h2 class="text-lg font-bold mt-5 mb-2" style="color:var(--text)">$1</h2>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\* (.*)/g, '<li class="ml-4 mb-1 list-disc">$1</li>')
    .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded text-sm font-mono" style="background:var(--panel-2);color:#de638a">$1</code>')
    .replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre class="code-block mt-3 mb-3 text-xs overflow-x-auto"><code>$1</code></pre>')
    .replace(/\n/g, '<br/>');

export const AIReviewCenter: React.FC = () => {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [response, setResponse] = useState<string | null>(null);
  const [responseTitle, setResponseTitle] = useState('');
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat]);

  const callAI = async (endpoint: string, actionLabel: string) => {
    if (!code.trim()) return;
    setLoading(true);
    setActiveAction(actionLabel);
    setResponse(null);
    try {
      const res = await fetch(`${API}/ai/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();
      setResponse(data.content ?? 'No response received.');
      setResponseTitle(actionLabel);
    } catch (e: any) {
      setResponse(e.message.includes('Failed to fetch')
        ? '❌ Cannot connect to backend. Start the FastAPI server on port 8000.'
        : `❌ Error: ${e.message}`);
      setResponseTitle('Error');
    } finally {
      setLoading(false);
      setActiveAction(null);
    }
  };

  const sendChat = async () => {
    const q = chatInput.trim();
    if (!q || chatLoading) return;
    setChatInput('');
    setChat(prev => [...prev, { role: 'user', content: q }]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API}/ai/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, question: q }),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      const data = await res.json();
      setChat(prev => [...prev, { role: 'assistant', content: data.content ?? 'No response.' }]);
    } catch (e: any) {
      setChat(prev => [...prev, { role: 'assistant', content: `❌ Error: ${e.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="space-y-6 page-enter">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-1">AI Review Center</h1>
        <p className="text-slate-500 dark:text-slate-400">
          Powered by Gemini. Get deep insights, refactoring suggestions, and code explanations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Left: Code Editor ── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Code2 size={16} style={{ color: '#de638a' }} />
              Source Code
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
              <button
                onClick={() => { setCode(SAMPLE_CODE); setLanguage('python'); setResponse(null); setChat([]); }}
                className="btn-ghost text-xs py-1.5 px-2"
                title="Load sample code"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          </div>

          <div className="panel overflow-hidden" style={{ background: '#0f0b1a', borderColor: '#2e2048' }}>
            <div className="flex items-center gap-1.5 px-4 py-2 border-b" style={{ borderColor: '#2e2048' }}>
              <span className="w-3 h-3 rounded-full bg-red-500/70" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
              <span className="w-3 h-3 rounded-full bg-green-500/70" />
              <span className="ml-2 text-xs font-mono" style={{ color: '#7a6a96' }}>editor.py</span>
            </div>
            <textarea
              value={code}
              onChange={e => setCode(e.target.value)}
              className="w-full resize-none outline-none font-mono text-sm p-4"
              style={{
                minHeight: '300px',
                background: 'transparent',
                color: '#e9d8ff',
                caretColor: '#de638a',
              }}
              spellCheck={false}
              placeholder="Paste your code here..."
            />
          </div>

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => callAI('review', 'Full Review')}
              disabled={loading}
              className="btn-primary flex-1 justify-center py-2.5 text-sm"
            >
              {loading && activeAction === 'Full Review' ? <><span className="spinner" /> Analyzing...</> : <><Sparkles size={15} /> Review Code</>}
            </button>
            <button
              onClick={() => callAI('explain', 'Explanation')}
              disabled={loading}
              className="btn-ghost text-sm py-2.5 px-4"
            >
              {loading && activeAction === 'Explanation' ? <span className="spinner" style={{ borderTopColor: 'var(--text)' }} /> : 'Explain'}
            </button>
            <button
              onClick={() => callAI('refactor', 'Refactoring')}
              disabled={loading}
              className="btn-ghost text-sm py-2.5 px-4"
            >
              {loading && activeAction === 'Refactoring' ? <span className="spinner" style={{ borderTopColor: 'var(--text)' }} /> : 'Refactor'}
            </button>
          </div>
        </div>

        {/* ── Right: AI Output + Chat ── */}
        <div className="space-y-3">
          <h2 className="text-base font-bold flex items-center gap-2">
            <Bot size={16} style={{ color: '#de638a' }} />
            AI Response {responseTitle && <span className="text-xs font-normal px-2 py-0.5 rounded-full" style={{ background: 'var(--panel-2)', color: 'var(--text-muted)' }}>— {responseTitle}</span>}
          </h2>

          {/* Response area */}
          <div className="panel p-5 overflow-y-auto" style={{ minHeight: '200px', maxHeight: '300px' }}>
            {!response && !loading && (
              <div className="h-full flex flex-col items-center justify-center py-8" style={{ color: 'var(--text-faint)' }}>
                <Bot size={40} className="mb-3 opacity-40" />
                <p className="text-sm">Click "Review Code", "Explain", or "Refactor" to get AI insights</p>
              </div>
            )}
            {loading && (
              <div className="h-full flex flex-col items-center justify-center py-8" style={{ color: '#de638a' }}>
                <div className="mb-3">
                  <Sparkles size={40} className="animate-pulse" />
                </div>
                <div className="flex items-center gap-3 text-slate-400">
                <p className="text-sm font-semibold">Gemini is thinking<span className="cursor" /></p>
                </div>
              </div>
            )}
            {response && !loading && (
              <div
                className="prose max-w-none text-sm leading-relaxed"
                style={{ color: 'var(--text)' }}
                dangerouslySetInnerHTML={{ __html: renderMd(response) }}
              />
            )}
          </div>

          {/* Chat section */}
          <div className="panel overflow-hidden">
            <div className="px-4 py-2 border-b text-xs font-semibold uppercase tracking-wider" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
              Follow-up Chat
            </div>
            <div className="overflow-y-auto p-4 space-y-3" style={{ minHeight: '120px', maxHeight: '200px' }}>
              {chat.length === 0 && (
                <p className="text-xs text-center py-4" style={{ color: 'var(--text-faint)' }}>Ask a follow-up question about your code...</p>
              )}
              {chat.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className="max-w-[85%] px-3 py-2 rounded-xl text-sm"
                    style={{
                      background: m.role === 'user' ? 'linear-gradient(135deg, #6d3d8e, #4a3267)' : 'var(--panel-2)',
                      color: m.role === 'user' ? '#fff' : 'var(--text)',
                    }}
                    dangerouslySetInnerHTML={{ __html: renderMd(m.content) }}
                  />
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="px-3 py-2 rounded-xl text-sm" style={{ background: 'var(--panel-2)', color: 'var(--text-muted)' }}>
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <span className="animate-pulse">Gemini is typing...</span>
                  </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat input */}
            <div className="p-3 border-t flex gap-2" style={{ borderColor: 'var(--border)' }}>
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendChat()}
                placeholder="Ask a follow-up question..."
                className="input-field text-sm py-2"
                style={{ borderRadius: '10px' }}
              />
              <button
                onClick={sendChat}
                disabled={chatLoading || !chatInput.trim()}
                className="btn-primary py-2 px-3"
                style={{ borderRadius: '10px', minWidth: '40px' }}
              >
                {chatLoading ? <span className="spinner w-4 h-4" /> : <Send size={15} />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
