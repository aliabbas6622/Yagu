import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import IdeaCard from './components/IdeaCard';
import Stats from './components/Stats';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import IdeaPlaygroundDrawer from './components/IdeaPlaygroundDrawer';
import ScraperStatusConsole from './components/ScraperStatusConsole';
import ScrapersMonitor from './pages/ScrapersMonitor';
import { Search, SlidersHorizontal, AlertCircle, Compass, BarChart2, Radio } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('explore'); // explore | analytics
  const [ideas, setIdeas] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Scraper status polling state
  const [scraperStatus, setScraperStatus] = useState(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [pollInterval, setPollInterval] = useState(null);

  // Active selected idea for side drawer
  const [selectedIdea, setSelectedIdea] = useState(null);

  // Filter and Search states
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const fetchIdeas = async () => {
    try {
      setLoading(true);
      const [ideasRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/ideas`),
        axios.get(`${API_BASE_URL}/stats`)
      ]);
      setIdeas(ideasRes.data);
      setStats(statsRes.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load ideas. Make sure the backend API server is running and reachable.');
    } finally {
      setLoading(false);
    }
  };

  const fetchScraperStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/scraper/status`);
      setScraperStatus(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching scraper status:', err);
      return null;
    }
  };

  // Initial load
  useEffect(() => {
    fetchIdeas();
    fetchScraperStatus();
  }, []);

  // Poll status when active
  useEffect(() => {
    const statusVal = scraperStatus?.status;
    const isRunning = statusVal === 'active';

    if (isRunning && !pollInterval) {
      const interval = setInterval(async () => {
        const latest = await fetchScraperStatus();
        if (latest && latest.status === 'idle') {
          // Finished! Refresh list
          fetchIdeas();
          clearInterval(interval);
          setPollInterval(null);
        }
      }, 1500);
      setPollInterval(interval);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
    };
  }, [scraperStatus]);

  const handleTriggerScraper = async () => {
    if (scraperStatus?.status === 'active') return;

    try {
      setIsTriggering(true);
      // Clean up previous interval if it exists
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }

      await axios.post(`${API_BASE_URL}/trigger`);
      
      // Fetch initial active state and begin polling
      const initialStatus = await fetchScraperStatus();
      setScraperStatus(initialStatus);
    } catch (err) {
      console.error('Error triggering scraper:', err);
      setError('Failed to trigger the agentic scraper pipeline.');
    } finally {
      setIsTriggering(false);
    }
  };

  // Extract unique categories for filter options
  const uniqueCategories = ['all', ...new Set(ideas.map(idea => idea.category).filter(Boolean))];

  const filteredIdeas = ideas
    .filter(idea => {
      const matchesSearch = 
        idea.post_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        idea.problem_summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        idea.category.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = categoryFilter === 'all' || idea.category === categoryFilter;

      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      if (sortBy === 'score') return b.total_score - a.total_score;
      if (sortBy === 'newest') return new Date(b.date_found) - new Date(a.date_found);
      if (sortBy === 'urgency') return b.urgency_score - a.urgency_score;
      if (sortBy === 'monetization') return b.monetization_score - a.monetization_score;
      return 0;
    });

  const isScraperActive = scraperStatus?.status === 'active';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col font-sans select-none antialiased">
      <Header
        onRefresh={handleTriggerScraper}
        isRefreshing={isScraperActive}
        stats={stats}
      />

      {/* Main navigation tabs */}
      <div className="border-b border-slate-900 bg-slate-900/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-6">
          <button
            onClick={() => setActiveTab('explore')}
            className={`flex items-center space-x-2 py-4 border-b-2 font-bold text-xs uppercase tracking-wider transition-colors ${
              activeTab === 'explore' 
                ? 'border-indigo-500 text-indigo-400' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Compass className="h-4 w-4" />
            <span>Opportunities Hub</span>
          </button>
          
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center space-x-2 py-4 border-b-2 font-bold text-xs uppercase tracking-wider transition-colors ${
              activeTab === 'analytics' 
                ? 'border-indigo-500 text-indigo-400' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart2 className="h-4 w-4" />
            <span>Analytics Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('scrapers')}
            className={`flex items-center space-x-2 py-4 border-b-2 font-bold text-xs uppercase tracking-wider transition-colors ${
              activeTab === 'scrapers'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="h-4 w-4" />
            <span>Scrapers Monitor</span>
          </button>
        </div>
      </div>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 select-text">
        {error && (
          <div className="bg-red-950/20 border border-red-900/30 rounded-xl p-4 flex items-start space-x-3 mb-6">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-extrabold text-red-400">Database Connection Error</h4>
              <p className="text-xs text-red-300/80 leading-relaxed mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Tab 1: Explore Opportunities */}
        {activeTab === 'explore' && (
          <div className="space-y-6">
            {/* Scraper controller widget */}
            <ScraperStatusConsole 
              statusData={scraperStatus} 
              onTrigger={handleTriggerScraper}
              isTriggering={isTriggering}
            />

            {/* Quick Metrics display */}
            {ideas.length > 0 && <Stats ideas={ideas} />}

            {/* Search, Filter, Sort Controls */}
            <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter keywords, categories, target users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-lg py-2 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-slate-350"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center space-x-2">
                  <SlidersHorizontal className="h-3.5 w-3.5 text-slate-500" />
                  <span className="text-[11px] font-bold text-slate-400 uppercase">Sort By:</span>
                </div>
                
                {/* Sort dropdown */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 cursor-pointer"
                >
                  <option value="score">Opportunity Score</option>
                  <option value="newest">Latest Found</option>
                  <option value="urgency">Highest Urgency</option>
                  <option value="monetization">Highest Monetization</option>
                </select>

                {/* Category filter */}
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 cursor-pointer capitalize"
                >
                  {uniqueCategories.map(cat => (
                    <option key={cat} value={cat}>
                      {cat === 'all' ? 'All Categories' : cat.replace('-', ' ')}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Opportunity Cards list */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-850 rounded-xl h-64 animate-pulse"></div>
                ))}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredIdeas.map((idea) => (
                    <div 
                      key={idea.id || idea.original_url}
                      onClick={() => setSelectedIdea(idea)}
                      className="cursor-pointer"
                    >
                      <IdeaCard idea={idea} />
                    </div>
                  ))}
                </div>

                {filteredIdeas.length === 0 && (
                  <div className="text-center py-20 bg-slate-900/10 border border-dashed border-slate-850 rounded-xl">
                    <p className="text-slate-500 text-xs italic">No opportunities match the filtered criteria.</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Tab 2: Analytics Dashboard */}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard ideas={ideas} />
        )}

        {/* Tab 3: Scrapers Monitor */}
        {activeTab === 'scrapers' && (
          <ScrapersMonitor />
        )}
      </main>

      {/* Idea Playground Side Drawer */}
      {selectedIdea && (
        <>
          {/* Backdrop overlay */}
          <div 
            onClick={() => setSelectedIdea(null)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-in fade-in duration-200"
          />
          <IdeaPlaygroundDrawer 
            idea={selectedIdea} 
            onClose={() => setSelectedIdea(null)} 
          />
        </>
      )}
    </div>
  );
}

export default App;
