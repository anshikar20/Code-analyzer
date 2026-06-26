import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, CheckCircle2, XCircle, Search, X, Save } from 'lucide-react';

interface CustomRule {
  name: string;
  language: string;
  type: string;
  pattern: string;
  severity: string;
  message: string;
  enabled: boolean;
}

const EMPTY_RULE: CustomRule = {
  name: '', language: 'any', type: 'regex', pattern: '', severity: 'warning', message: '', enabled: true,
};

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Modal ──────────────────────────────────────────────────────
const RuleModal: React.FC<{
  initial?: CustomRule;
  onSave: (r: CustomRule) => void;
  onClose: () => void;
}> = ({ initial, onSave, onClose }) => {
  const [form, setForm] = useState<CustomRule>(initial ?? EMPTY_RULE);
  const [err, setErr] = useState('');

  const set = (k: keyof CustomRule, v: any) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSave = () => {
    if (!form.name.trim() || !form.pattern.trim() || !form.message.trim()) {
      setErr('Name, Pattern, and Message are required.'); return;
    }
    onSave(form);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="panel w-full max-w-lg"
        style={{ background: 'var(--panel)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-lg font-bold">{initial ? 'Edit Rule' : 'Create New Rule'}</h3>
          <button onClick={onClose} className="btn-ghost p-1.5" style={{ borderRadius: '8px', padding: '6px' }}>
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {err && <p className="text-sm font-medium" style={{ color: '#de638a' }}>{err}</p>}

          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                Rule Name *
              </label>
              <input className="input-field" value={form.name} onChange={e => set('name', e.target.value)} placeholder="e.g. No hardcoded passwords" />
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Language</label>
              <select className="input-field" value={form.language} onChange={e => set('language', e.target.value)}>
                {['any', 'python', 'java', 'cpp'].map(l => <option key={l}>{l}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Severity</label>
              <select className="input-field" value={form.severity} onChange={e => set('severity', e.target.value)}>
                {['error', 'warning', 'info'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Type</label>
              <select className="input-field" value={form.type} onChange={e => set('type', e.target.value)}>
                {['regex', 'contains', 'startswith'].map(t => <option key={t}>{t}</option>)}
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Pattern *</label>
              <input className="input-field font-mono text-sm" value={form.pattern} onChange={e => set('pattern', e.target.value)} placeholder="e.g. password\s*=\s*[quote][^quote]+" />
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Violation Message *</label>
              <input className="input-field" value={form.message} onChange={e => set('message', e.target.value)} placeholder="e.g. Potential hardcoded credential detected." />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 p-5 border-t" style={{ borderColor: 'var(--border)' }}>
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button onClick={handleSave} className="btn-primary text-sm">
            <Save size={14} />Save Rule
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Page ──────────────────────────────────────────────────
export const RuleManagement: React.FC = () => {
  const [rules, setRules] = useState<CustomRule[]>([
    { name: 'No hardcoded credentials', language: 'any', type: 'regex', pattern: "(?i)(password|secret|key)\\s*=\\s*[\"'][^\"']+[\"']", severity: 'error', message: 'Potential hardcoded credential detected.', enabled: true },
    { name: 'Avoid console.log', language: 'any', type: 'contains', pattern: 'console.log(', severity: 'warning', message: 'Remove console.log before committing.', enabled: true },
  ]);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editIdx, setEditIdx] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API}/custom-rules`)
      .then(res => res.json())
      .then(data => setRules(data.rules || []))
      .catch(err => console.error("Failed to load rules", err));
  }, []);

  const toggle = async (i: number) => {
    const oldRules = [...rules];
    setRules(r => r.map((rule, idx) => idx === i ? { ...rule, enabled: !rule.enabled } : rule));
    try {
      await fetch(`${API}/custom-rules/${i}/toggle`, { method: 'PATCH' });
    } catch {
      setRules(oldRules);
    }
  };

  const del = async (i: number) => {
    const oldRules = [...rules];
    setRules(r => r.filter((_, idx) => idx !== i));
    try {
      await fetch(`${API}/custom-rules/${i}`, { method: 'DELETE' });
    } catch {
      setRules(oldRules);
    }
  };

  const openEdit = (i: number) => { setEditIdx(i); setShowModal(true); };
  const openCreate = () => { setEditIdx(null); setShowModal(true); };

  const handleSave = async (r: CustomRule) => {
    if (editIdx !== null) {
      setRules(prev => prev.map((rule, i) => i === editIdx ? r : rule));
      await fetch(`${API}/custom-rules/${editIdx}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(r),
      }).catch(() => {});
    } else {
      setRules(prev => [...prev, r]);
      await fetch(`${API}/custom-rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(r),
      }).catch(() => {});
    }
    setShowModal(false);
    setEditIdx(null);
  };

  const filtered = rules.filter(r =>
    r.name.toLowerCase().includes(search.toLowerCase()) ||
    r.message.toLowerCase().includes(search.toLowerCase())
  );

  const severityBadge = (s: string) => {
    const map: Record<string, string> = { error: 'badge badge-error', warning: 'badge badge-warning', info: 'badge badge-info' };
    return map[s] ?? 'badge badge-info';
  };

  return (
    <div className="space-y-6 page-enter">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-1">Rule Management</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Create and manage custom analysis rules for your team.</p>
        </div>
        <button onClick={openCreate} className="btn-primary shrink-0">
          <Plus size={16} /> Create New Rule
        </button>
      </div>

      {/* Search bar */}
      <div className="panel p-3">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-faint)' }} />
          <input
            type="text"
            placeholder="Search rules..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-9 py-2 text-sm"
          />
        </div>
      </div>

      {/* Rules list */}
      <div className="panel overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center" style={{ color: 'var(--text-faint)' }}>
            <p>No rules found. {search ? 'Try a different search.' : 'Click the &quot;Create New Rule&quot; button to add one!'}</p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
            {filtered.map((rule, idx) => (
              <div
                key={idx}
                className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors"
                style={{ background: 'var(--panel)' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--panel-2)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--panel)')}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <h3 className="font-bold text-[15px]">{rule.name}</h3>
                    <span className={severityBadge(rule.severity)}>{rule.severity}</span>
                    <span className="badge" style={{ background: 'var(--panel-2)', color: 'var(--text-muted)' }}>{rule.language}</span>
                    <span className="badge" style={{ background: 'var(--panel-2)', color: 'var(--text-muted)' }}>{rule.type}</span>
                  </div>
                  <p className="text-sm mb-2 line-clamp-1" style={{ color: 'var(--text-muted)' }}>{rule.message}</p>
                  <code className="text-xs font-mono px-2 py-1 rounded" style={{ background: 'var(--panel-2)', color: '#de638a' }}>
                    {rule.pattern}
                  </code>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => toggle(idx)}
                    style={rule.enabled
                      ? { background: '#059669', color: '#ffffff', border: 'none' }
                      : { background: 'var(--panel-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }
                    }
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer"
                  >
                    {rule.enabled ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                    {rule.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                  <button onClick={() => openEdit(idx)} className="btn-ghost p-2" style={{ borderRadius: '8px' }} title="Edit">
                    <Edit2 size={15} />
                  </button>
                  <button onClick={() => del(idx)} className="btn-ghost p-2" style={{ borderRadius: '8px', color: '#de638a' }} title="Delete">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <RuleModal
          initial={editIdx !== null ? rules[editIdx] : undefined}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditIdx(null); }}
        />
      )}
    </div>
  );
};
