import React, { useState } from 'react';
import { BarChart3, PieChart, TrendingUp, Grid, ExternalLink } from 'lucide-react';

const AnalyticsDashboard = ({ ideas }) => {
  const [hoveredIdea, setHoveredIdea] = useState(null);

  if (!ideas || ideas.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
        No ideas loaded yet. Trigger a scrape to collect some opportunities.
      </div>
    );
  }

  // Calculate statistics
  const totalIdeas = ideas.length;
  
  // Category breakdown
  const categoryCounts = ideas.reduce((acc, curr) => {
    const cat = curr.category || 'other';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  const categories = Object.keys(categoryCounts).map(cat => ({
    name: cat,
    count: categoryCounts[cat],
    percentage: ((categoryCounts[cat] / totalIdeas) * 100).toFixed(1)
  })).sort((a, b) => b.count - a.count);

  // Source breakdown
  const sourceCounts = ideas.reduce((acc, curr) => {
    const src = curr.source || 'unknown';
    acc[src] = (acc[src] || 0) + 1;
    return acc;
  }, {});

  const sources = Object.keys(sourceCounts).map(src => ({
    name: src.toUpperCase(),
    count: sourceCounts[src],
    percentage: ((sourceCounts[src] / totalIdeas) * 100).toFixed(1)
  }));

  // Matrix/Scatter data: Urgency vs Monetization (1-10)
  const matrixData = ideas.map(idea => ({
    id: idea.id,
    title: idea.post_title,
    urgency: idea.urgency_score || 1,
    monetization: idea.monetization_score || 1,
    score: idea.total_score || 0,
    category: idea.category,
    url: idea.original_url
  }));

  // For Donut Chart
  let accumulatedPercent = 0;
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6'];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Evaluated</p>
          <p className="text-3xl font-extrabold text-white mt-2">{totalIdeas}</p>
          <p className="text-xs text-slate-400 mt-1">Found across subreddits & forums</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Urgency</p>
          <p className="text-3xl font-extrabold text-amber-400 mt-2">
            {(ideas.reduce((acc, curr) => acc + (curr.urgency_score || 0), 0) / totalIdeas).toFixed(1)}/10
          </p>
          <p className="text-xs text-slate-400 mt-1">Product pain points urgency level</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Monetization</p>
          <p className="text-3xl font-extrabold text-emerald-400 mt-2">
            {(ideas.reduce((acc, curr) => acc + (curr.monetization_score || 0), 0) / totalIdeas).toFixed(1)}/10
          </p>
          <p className="text-xs text-slate-400 mt-1">Average commercial potential score</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">High Opportunity (Score &ge; 25)</p>
          <p className="text-3xl font-extrabold text-indigo-400 mt-2">
            {ideas.filter(idea => idea.total_score >= 25).length}
          </p>
          <p className="text-xs text-slate-400 mt-1">Premium startup ideas qualified</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Category Share (Detailed Bar list with SVG indicator) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center space-x-2 mb-6">
            <BarChart3 className="h-5 w-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white">Categories Breakdown</h2>
          </div>

          <div className="space-y-4">
            {categories.map((cat, idx) => (
              <div key={cat.name} className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-300 capitalize">{cat.name.replace('-', ' ')}</span>
                  <span className="text-slate-400">
                    {cat.count} {cat.count === 1 ? 'idea' : 'ideas'} ({cat.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500" 
                    style={{ 
                      width: `${cat.percentage}%`,
                      backgroundColor: colors[idx % colors.length]
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Source Share (Detailed Donut Chart in SVG) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center space-x-2 mb-6">
            <PieChart className="h-5 w-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white">Sources Distribution</h2>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
            {/* SVG Donut */}
            <div className="relative w-40 h-40">
              <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                {/* Background circle */}
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="#1e293b" strokeWidth="4" />
                
                {/* Colored segments */}
                {sources.map((src, idx) => {
                  const percent = parseFloat(src.percentage);
                  const strokeDash = `${percent} ${100 - percent}`;
                  const offset = 100 - accumulatedPercent;
                  accumulatedPercent += percent;
                  return (
                    <circle
                      key={src.name}
                      cx="18"
                      cy="18"
                      r="15.915"
                      fill="none"
                      stroke={colors[idx % colors.length]}
                      strokeWidth="4"
                      strokeDasharray={strokeDash}
                      strokeDashoffset={offset}
                      className="transition-all duration-500"
                    />
                  );
                })}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-black text-white">{totalIdeas}</span>
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Total</span>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-3 shrink-0">
              {sources.map((src, idx) => (
                <div key={src.name} className="flex items-center space-x-3 text-xs">
                  <div 
                    className="w-3.5 h-3.5 rounded-sm shrink-0" 
                    style={{ backgroundColor: colors[idx % colors.length] }}
                  />
                  <div>
                    <p className="font-bold text-slate-200">{src.name}</p>
                    <p className="text-[10px] text-slate-500">
                      {src.count} ideas ({src.percentage}%)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Score Grid: Matrix of Urgency vs. Monetization */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Grid className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold text-white">Validation Opportunity Matrix</h2>
              <p className="text-xs text-slate-500">Map of Urgency (need) vs. Monetization potential (budget)</p>
            </div>
          </div>
          <div className="hidden sm:block text-[11px] bg-slate-800 text-slate-400 px-3 py-1 rounded-full font-medium">
            Top-Right section = Immediate MVP Candidates
          </div>
        </div>

        {/* 2D Interactive Scatter Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-4">
          <div className="md:col-span-3">
            <div className="relative bg-slate-950 border border-slate-800/80 rounded-lg p-6">
              
              {/* Scatter SVG Plot area */}
              <div className="relative w-full aspect-[2/1] min-h-[220px]">
                {/* Horizontal grid lines */}
                {[...Array(5)].map((_, i) => (
                  <div 
                    key={i} 
                    className="absolute left-0 right-0 border-t border-slate-800/50" 
                    style={{ top: `${(i / 4) * 100}%` }}
                  />
                ))}
                {/* Vertical grid lines */}
                {[...Array(5)].map((_, i) => (
                  <div 
                    key={i} 
                    className="absolute top-0 bottom-0 border-l border-slate-800/50" 
                    style={{ left: `${(i / 4) * 100}%` }}
                  />
                ))}

                {/* Plot points */}
                {matrixData.map((pt) => {
                  // Normalize 1-10 to 0%-100%
                  const leftPercent = ((pt.urgency - 1) / 9) * 100;
                  const bottomPercent = ((pt.monetization - 1) / 9) * 100;

                  // High opportunity color
                  const isHigh = pt.score >= 25;
                  const dotColor = isHigh ? 'bg-indigo-500 ring-4 ring-indigo-500/20' : 'bg-slate-400 hover:bg-slate-200';

                  return (
                    <button
                      key={pt.id || pt.url}
                      onClick={() => {}}
                      onMouseEnter={() => setHoveredIdea(pt)}
                      onMouseLeave={() => setHoveredIdea(null)}
                      className={`absolute w-3.5 h-3.5 rounded-full -translate-x-1/2 translate-y-1/2 cursor-pointer transition-transform hover:scale-150 duration-150 ${dotColor}`}
                      style={{ 
                        left: `${leftPercent}%`, 
                        bottom: `${bottomPercent}%` 
                      }}
                      aria-label={pt.title}
                    />
                  );
                })}

                {/* Y-Axis Label */}
                <div className="absolute -left-10 top-1/2 -rotate-90 origin-center text-[10px] uppercase tracking-wider font-extrabold text-slate-500">
                  Monetization &rarr;
                </div>

                {/* X-Axis Label */}
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] uppercase tracking-wider font-extrabold text-slate-500">
                  Urgency (Problem Intensity) &rarr;
                </div>
              </div>

              {/* Ticks representation */}
              <div className="flex justify-between text-[10px] font-bold text-slate-600 mt-2 px-1">
                <span>Low Urgency (1)</span>
                <span>High Urgency (10)</span>
              </div>
            </div>
          </div>

          {/* Hover Details Panel */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
            {hoveredIdea ? (
              <div className="space-y-3 animate-in fade-in duration-100">
                <span className="text-[10px] font-extrabold uppercase bg-indigo-600/20 text-indigo-400 px-2 py-0.5 rounded">
                  {hoveredIdea.category || 'general'}
                </span>
                <h4 className="text-xs font-bold text-white line-clamp-3">
                  {hoveredIdea.title}
                </h4>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Urgency:</span>
                    <span className="text-amber-400 font-bold">{hoveredIdea.urgency}/10</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Monetization:</span>
                    <span className="text-emerald-400 font-bold">{hoveredIdea.monetization}/10</span>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-850">
                  <span className="text-[10px] text-slate-500 block">Total Score:</span>
                  <span className="text-sm font-extrabold text-white">{hoveredIdea.score}/30</span>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col justify-center items-center text-center py-6 text-slate-500">
                <TrendingUp className="h-8 w-8 text-slate-700 mb-2" />
                <p className="text-xs italic">Hover over the dots on the matrix to see specific product validation metrics.</p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default AnalyticsDashboard;
