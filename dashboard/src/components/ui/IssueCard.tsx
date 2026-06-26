import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';

export type Severity = 'critical' | 'error' | 'warning' | 'info' | 'success';

interface IssueCardProps {
  title: string;
  message: string;
  severity: Severity;
  source?: string;
  ruleId?: string;
  line?: number;
  suggestion?: string;
}

export const IssueCard: React.FC<IssueCardProps> = ({ 
  title, message, severity, source, ruleId, line, suggestion 
}) => {
  const [expanded, setExpanded] = useState(false);

  const colors = {
    critical: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/30 dark:border-red-900/50 dark:text-red-300',
    error: 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/30 dark:border-rose-900/50 dark:text-rose-300',
    warning: 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-900/50 dark:text-amber-300',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950/30 dark:border-blue-900/50 dark:text-blue-300',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-900/50 dark:text-emerald-300',
  };

  const Icon = {
    critical: AlertCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
    success: CheckCircle2,
  }[severity];

  return (
    <div className={clsx("rounded-xl border p-4 transition-all", colors[severity])}>
      <div 
        className="flex items-start gap-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <Icon className="mt-0.5 shrink-0" size={20} />
        
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-[15px]">{title}</h4>
            <div className="flex items-center gap-2">
              {line && <span className="text-xs opacity-70 font-mono">Line {line}</span>}
              <button className="opacity-50 hover:opacity-100 transition-opacity">
                {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
            </div>
          </div>
          
          <p className={clsx("text-sm mt-1 opacity-90", !expanded && "line-clamp-1")}>
            {message}
          </p>
          
          {expanded && (
            <div className="mt-4 space-y-3">
              {suggestion && (
                <div className="bg-white/50 dark:bg-black/20 p-3 rounded-lg border border-inherit border-opacity-50 text-sm">
                  <span className="font-semibold opacity-80 block mb-1">Suggestion</span>
                  {suggestion}
                </div>
              )}
              
              <div className="flex items-center gap-2 text-xs font-mono opacity-70">
                {source && <span>Source: {source}</span>}
                {source && ruleId && <span>•</span>}
                {ruleId && <span>Rule: {ruleId}</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
