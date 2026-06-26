import React from 'react';
import clsx from 'clsx';

interface ScoreCardProps {
  title: string;
  score: number;
  description: string;
  className?: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({ title, score, description, className }) => {
  // Determine color based on score
  const colorClass = 
    score >= 90 ? 'text-green-500' :
    score >= 70 ? 'text-yellow-500' :
    'text-red-500';

  const ringClass = 
    score >= 90 ? 'ring-green-500/30' :
    score >= 70 ? 'ring-yellow-500/30' :
    'ring-red-500/30';

  return (
    <div className={clsx(
      "bg-[var(--panel-bg)] border border-[var(--border-color)] rounded-2xl p-6 shadow-sm flex flex-col items-center text-center",
      className
    )}>
      <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 mb-2">{title}</h3>
      
      <div className={clsx(
        "relative w-24 h-24 rounded-full flex items-center justify-center mb-4 ring-4",
        ringClass
      )}>
        <span className={clsx("text-3xl font-bold", colorClass)}>
          {score}
        </span>
      </div>
      
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
};
