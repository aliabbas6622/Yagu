import React from 'react';
import { Target, Zap, DollarSign } from 'lucide-react';

const Stats = ({ ideas }) => {
  const avgUrgency = (ideas.reduce((acc, curr) => acc + curr.urgency_score, 0) / ideas.length).toFixed(1);
  const avgFrequency = (ideas.reduce((acc, curr) => acc + curr.frequency_score, 0) / ideas.length).toFixed(1);
  const avgMonetization = (ideas.reduce((acc, curr) => acc + curr.monetization_score, 0) / ideas.length).toFixed(1);

  const statItems = [
    { label: 'Avg Urgency', value: avgUrgency, icon: Zap, color: 'text-amber-400' },
    { label: 'Avg Frequency', value: avgFrequency, icon: Target, color: 'text-blue-400' },
    { label: 'Avg Monetization', value: avgMonetization, icon: DollarSign, color: 'text-emerald-400' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      {statItems.map((item, idx) => (
        <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{item.label}</p>
              <p className="text-2xl font-bold text-white mt-1">{item.value}</p>
            </div>
            <div className={`p-2 rounded-lg bg-slate-800 ${item.color}`}>
              <item.icon className="h-5 w-5" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Stats;
