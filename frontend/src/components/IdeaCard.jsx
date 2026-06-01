import React from 'react';
import { ExternalLink, TrendingUp, Clock, User, Tag } from 'lucide-react';

const IdeaCard = ({ idea }) => {
  const getScoreColor = (score) => {
    if (score >= 25) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (score >= 20) return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all group">
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center space-x-2">
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getScoreColor(idea.total_score)}`}>
              Score: {idea.total_score}
            </span>
            <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
              {idea.source}
            </span>
          </div>
          <a
            href={idea.original_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-white transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>

        <h3 className="text-lg font-bold text-white mb-2 line-clamp-1 group-hover:text-indigo-400 transition-colors">
          {idea.post_title}
        </h3>

        <p className="text-slate-400 text-sm mb-4 line-clamp-2">
          {idea.problem_summary}
        </p>

        <div className="space-y-3 mb-6">
          {idea.product_ideas.slice(0, 2).map((p, idx) => (
            <div key={idx} className="bg-slate-800/50 rounded-lg p-3 border border-slate-800">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-indigo-300">{p.type}</span>
              </div>
              <p className="text-xs text-slate-300 font-medium">{p.idea}</p>
              <p className="text-[10px] text-slate-500 mt-1">{p.description}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800/50">
          <div className="flex items-center text-[11px] text-slate-500">
            <Tag className="h-3 w-3 mr-1.5 text-slate-600" />
            <span className="truncate">{idea.category}</span>
          </div>
          <div className="flex items-center text-[11px] text-slate-500">
            <User className="h-3 w-3 mr-1.5 text-slate-600" />
            <span className="truncate">{idea.target_audience}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IdeaCard;
