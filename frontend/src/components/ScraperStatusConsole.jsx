import React, { useEffect, useRef } from 'react';
import { Terminal, RefreshCw, CheckCircle, AlertCircle, Play } from 'lucide-react';

const ScraperStatusConsole = ({ statusData, onTrigger, isTriggering }) => {
  const logEndRef = useRef(null);

  // Auto scroll logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [statusData?.logs]);

  if (!statusData) return null;

  const { status, current_step, progress, logs, stats, error } = statusData;
  const isActive = status === 'active';

  // Determine active stepper indices
  const getStepStatus = (stepIndex) => {
    // Steps mapping:
    // 0: Scraping (progress 10-34)
    // 1: Deduping (progress 35-49)
    // 2: Analyzing (progress 50-84)
    // 3: Saving (progress 85-99)
    // Completed (progress 100)
    if (progress === 100) return 'completed';
    if (error) return 'failed';

    if (stepIndex === 0) {
      if (progress >= 35) return 'completed';
      if (progress >= 10) return 'active';
    }
    if (stepIndex === 1) {
      if (progress >= 50) return 'completed';
      if (progress >= 35) return 'active';
    }
    if (stepIndex === 2) {
      if (progress >= 85) return 'completed';
      if (progress >= 50) return 'active';
    }
    if (stepIndex === 3) {
      if (progress >= 100) return 'completed';
      if (progress >= 85) return 'active';
    }
    return 'pending';
  };

  const getStepClass = (stepStatus) => {
    if (stepStatus === 'completed') return 'border-emerald-500 text-emerald-400 bg-emerald-950/20';
    if (stepStatus === 'active') return 'border-indigo-500 text-indigo-400 bg-indigo-950/30 animate-pulse';
    return 'border-slate-800 text-slate-500 bg-slate-900/30';
  };

  const formatTimestamp = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 space-y-5 animate-in fade-in duration-300">
      
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${isActive ? 'bg-indigo-950 text-indigo-400' : 'bg-slate-800 text-slate-400'}`}>
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white flex items-center space-x-2">
              <span>Agentic Scraper Console</span>
              {isActive && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-indigo-900/40 text-indigo-400 border border-indigo-900/30">
                  Running Pipeline
                </span>
              )}
            </h3>
            <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
              {isActive ? `Step: ${current_step}` : 'Console idle. Ready for discovery run.'}
            </p>
          </div>
        </div>

        {/* Trigger Button */}
        <button
          onClick={onTrigger}
          disabled={isActive || isTriggering}
          className="bg-indigo-650 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors text-xs font-bold flex items-center justify-center space-x-2 shrink-0 shadow-md"
        >
          {isActive || isTriggering ? (
            <>
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              <span>Scraping Sources...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Trigger Discovery Scraper</span>
            </>
          )}
        </button>
      </div>

      {/* Progress Bar & Stepper */}
      {isActive && (
        <div className="space-y-4 pt-2">
          {/* Progress bar */}
          <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-900">
            <div 
              className="h-full bg-indigo-650 rounded-full transition-all duration-500 ease-out" 
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Stepper Steps */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[10px] font-black uppercase tracking-wider">
            {[
              { idx: 0, label: '1. Scrape Forums' },
              { idx: 1, label: '2. Dedup Records' },
              { idx: 2, label: '3. AI Analysis' },
              { idx: 3, label: '4. Save Ideas' }
            ].map(step => {
              const stepStatus = getStepStatus(step.idx);
              return (
                <div 
                  key={step.idx} 
                  className={`p-2.5 rounded-lg border text-center font-bold ${getStepClass(stepStatus)}`}
                >
                  {step.label}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Terminal Output */}
      {logs && logs.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-[10px] text-slate-500 font-bold uppercase tracking-wider">
            <span>Execution Logs</span>
            {stats && (
              <div className="flex items-center space-x-3">
                <span>Scraped: <strong className="text-slate-300">{stats.scraped || 0}</strong></span>
                <span>Saved: <strong className="text-emerald-400">{stats.saved || 0}</strong></span>
              </div>
            )}
          </div>
          
          <div className="bg-slate-950 border border-slate-850 rounded-lg p-4 font-mono text-[11px] leading-relaxed max-h-48 overflow-y-auto space-y-1 select-text scrollbar-thin">
            {logs.map((log, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-slate-400">
                <span className="text-slate-600 shrink-0 select-none">[{formatTimestamp(log.timestamp)}]</span>
                <span className={log.message.includes('→') ? 'text-indigo-400 font-semibold' : log.message.includes('error') ? 'text-red-400' : 'text-slate-300'}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      )}

      {/* Completion alert status */}
      {!isActive && progress === 100 && !error && (
        <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-lg p-3.5 flex items-center space-x-3 text-xs text-emerald-400">
          <CheckCircle className="h-4.5 w-4.5 shrink-0" />
          <span>Last scraper run completed successfully. Fresh product opportunities are now updated.</span>
        </div>
      )}

      {error && (
        <div className="bg-red-950/20 border border-red-900/30 rounded-lg p-3.5 flex items-center space-x-3 text-xs text-red-400">
          <AlertCircle className="h-4.5 w-4.5 shrink-0" />
          <span>Scraper run failed: {error}. Check terminal logs or settings.</span>
        </div>
      )}

    </div>
  );
};

export default ScraperStatusConsole;
