import React from 'react';
import { Lightbulb, RefreshCw, BarChart3 } from 'lucide-react';

const Header = ({ onRefresh, isRefreshing, stats }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Lightbulb className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">IdeaMiner</h1>
              <p className="text-xs text-slate-400">AI-Powered Product Opportunities</p>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            {stats && (
              <div className="hidden md:flex items-center space-x-4 text-sm">
                <div className="flex items-center text-slate-300">
                  <BarChart3 className="h-4 w-4 mr-1 text-indigo-400" />
                  <span>{stats.total_ideas} Ideas found</span>
                </div>
                <div className="h-4 w-px bg-slate-700"></div>
                <div className="text-slate-300">
                  Avg Score: <span className="text-indigo-400 font-semibold">{stats.average_score}</span>
                </div>
              </div>
            )}

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? 'Scraping...' : 'Trigger Scraper'}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
