import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export const Analytics: React.FC = () => {
  const [trendData, setTrendData] = useState<any[]>([
    { time: 'Loading...', issues: 0, security: 0, quality: 0 }
  ]);
  const [categoryData, setCategoryData] = useState<any[]>([
    { name: 'Security', value: 0 },
    { name: 'Quality', value: 0 },
    { name: 'Performance', value: 0 },
    { name: 'Style', value: 0 },
  ]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/analytics`)
      .then(res => res.json())
      .then(data => {
        if (data.trendData && data.trendData.length > 0) {
          setTrendData(data.trendData);
        } else {
          setTrendData([{ time: 'No Data', issues: 0, security: 0, quality: 0 }]);
        }
        if (data.categoryData) {
          setCategoryData(data.categoryData);
        }
      })
      .catch(err => console.error("Failed to fetch analytics", err));
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold mb-2">Analytics</h1>
        <p className="text-slate-500 dark:text-slate-400">
          Historical trends and issue distribution across your codebase.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[var(--panel-bg)] border border-[var(--border-color)] rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Issue Trends (Last 10 Scans)</h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                <XAxis dataKey="time" stroke="currentColor" className="text-slate-400 text-xs" tickLine={false} axisLine={false} />
                <YAxis stroke="currentColor" className="text-slate-400 text-xs" tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                />
                <Legend />
                <Line type="monotone" dataKey="issues" name="Total Issues" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="security" name="Security" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="quality" name="Quality" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[var(--panel-bg)] border border-[var(--border-color)] rounded-2xl p-6">
          <h2 className="text-xl font-bold mb-6">Issues by Category (All-Time)</h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                <XAxis type="number" stroke="currentColor" className="text-slate-400 text-xs" tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" stroke="currentColor" className="text-slate-400 text-xs" tickLine={false} axisLine={false} width={110} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                  cursor={{ fill: 'var(--border-color)', opacity: 0.4 }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
