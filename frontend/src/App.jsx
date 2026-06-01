import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import IdeaCard from './components/IdeaCard';
import Stats from './components/Stats';
import { Search, SlidersHorizontal, AlertCircle } from 'lucide-react';

// Use environment variable for API URL or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function App() {
  const [ideas, setIdeas] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('score');

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
      setError('Failed to load ideas. Make sure the backend is running and reachable.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdeas();
  }, []);

  const handleTriggerScraper = async () => {
    try {
      setRefreshing(true);
      await axios.post(`${API_BASE_URL}/trigger`);
      // Optional: Show a toast notification
      setTimeout(() => setRefreshing(false), 3000);
    } catch (err) {
      console.error('Error triggering scraper:', err);
      setRefreshing(false);
    }
  };

  const filteredIdeas = ideas
    .filter(idea =>
      idea.post_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      idea.problem_summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      idea.category.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'score') return b.total_score - a.total_score;
      if (sortBy === 'newest') return new Date(b.date_found) - new Date(a.date_found);
      return 0;
    });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <Header
        onRefresh={handleTriggerScraper}
        isRefreshing={refreshing}
        stats={stats}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search ideas, problems, or categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
            />
          </div>

          <div className="flex items-center space-x-3">
            <SlidersHorizontal className="h-4 w-4 text-slate-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            >
              <option value="score">Top Scored</option>
              <option value="newest">Latest Found</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start space-x-3 mb-8">
            <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-red-500">Error</h4>
              <p className="text-sm text-red-400/80">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl h-64 animate-pulse"></div>
            ))}
          </div>
        ) : (
          <>
            {ideas.length > 0 && <Stats ideas={ideas} />}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredIdeas.map((idea) => (
                <IdeaCard key={idea.id || idea.original_url} idea={idea} />
              ))}
            </div>

            {!loading && filteredIdeas.length === 0 && (
              <div className="text-center py-20">
                <p className="text-slate-500 italic">No ideas found matching your criteria.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
