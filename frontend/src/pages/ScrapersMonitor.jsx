import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Radio, Globe, Briefcase, ShoppingBag, Star, Search,
  RefreshCw, CheckCircle2, XCircle, AlertCircle, Loader2, Clock,
  ExternalLink, ChevronDown, ChevronUp, Play, Zap
} from 'lucide-react'
import { api } from '../lib/api'
import EmptyState from '../components/EmptyState'

const SOURCE_META = {
  reddit:       { label: 'Reddit',        icon: '🟠', color: '#f97316', badge: 'badge-amber', desc: 'Pain points & feature requests from SaaS subreddits' },
  hn:           { label: 'Hacker News',   icon: '🔶', color: '#f59e0b', badge: 'badge-amber', desc: 'Ask HN posts and tech discussions' },
  github:       { label: 'GitHub Issues', icon: '⚫', color: '#e2e8f0', badge: 'badge-slate', desc: 'Open issues from popular repositories via GitHub API' },
  product_hunt: { label: 'Product Hunt',  icon: '🔴', color: '#ef4444', badge: 'badge-rose',  desc: 'Daily launches via Atom RSS feed fallback' },
  fiverr:       { label: 'Fiverr',        icon: '🟢', color: '#10b981', badge: 'badge-green', desc: 'Popular service gigs via Playwright crawler' },
  upwork:       { label: 'Upwork',        icon: '🔵', color: '#14b8a6', badge: 'badge-sky',   desc: 'Job postings via Playwright with stealth mode' },
  g2:           { label: 'G2 Reviews',    icon: '🔴', color: '#f43f5e', badge: 'badge-rose',  desc: 'Software reviews (Playwright, low rate)' },
  capterra:     { label: 'Capterra',      icon: '💙', color: '#3b82f6', badge: 'badge-blue',  desc: 'Software reviews via Playwright' },
  quora:        { label: 'Quora',         icon: '🟣', color: '#a855f7', badge: 'badge-violet', desc: 'Q&A searches via TinyFish API' },
}

const CRAWLER_TYPE = {
  reddit:       { type: 'PRAW + Scrapling fallback', reliability: 'High' },
  hn:           { type: 'BeautifulSoupCrawler',      reliability: 'High' },
  github:       { type: 'REST API + BSCrawler',      reliability: 'High' },
  product_hunt: { type: 'PlaywrightCrawler + RSS',   reliability: 'High' },
  fiverr:       { type: 'PlaywrightCrawler',         reliability: 'Medium' },
  upwork:       { type: 'PlaywrightCrawler',         reliability: 'Medium' },
  g2:           { type: 'PlaywrightCrawler',         reliability: 'Low' },
  capterra:     { type: 'PlaywrightCrawler',         reliability: 'Low' },
  quora:        { type: 'TinyFish API',              reliability: 'High' },
}

const RELIABILITY_COLORS = {
  High:   { text: '#6ee7b7', bg: 'rgba(16,185,129,0.12)',  badge: 'badge-green' },
  Medium: { text: '#fcd34d', bg: 'rgba(245,158,11,0.12)',  badge: 'badge-amber' },
  Low:    { text: '#fca5a5', bg: 'rgba(244,63,94,0.12)',   badge: 'badge-rose'  },
}

function SourceCard({ source, count, last_seen }) {
  const [expanded, setExpanded] = useState(false)
  const meta = SOURCE_META[source] || { label: source, icon: '📡', color: '#94a3b8', badge: 'badge-slate', desc: '' }
  const crawler = CRAWLER_TYPE[source] || { type: 'Unknown', reliability: 'Medium' }
  const rel = RELIABILITY_COLORS[crawler.reliability] || RELIABILITY_COLORS.Medium
  const hasData = (count || 0) > 0

  return (
    <div className={`card p-5 animate-fade-in transition-all ${hasData ? '' : 'opacity-60'}`}>
      <div className="flex items-start justify-between gap-3">
        {/* Icon + name */}
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
            style={{ background: `${meta.color}18`, border: `1px solid ${meta.color}30` }}
          >
            {meta.icon}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate" style={{ color: 'var(--text-primary)' }}>{meta.label}</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{meta.desc}</p>
          </div>
        </div>

        {/* Count + status */}
        <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
          <div className="flex items-center gap-1.5">
            {hasData
              ? <span className="badge badge-green flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Active</span>
              : <span className="badge badge-slate flex items-center gap-1"><AlertCircle className="w-3 h-3" /> No data</span>
            }
          </div>
          <p className="text-xl font-bold" style={{ color: meta.color }}>{count ?? 0}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>ideas saved</p>
        </div>
      </div>

      {/* Expand details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-4 w-full flex items-center justify-between text-xs py-1.5 px-2 rounded-lg transition-colors"
        style={{ color: 'var(--text-muted)', background: 'rgba(255,255,255,0.03)' }}
      >
        <span>Details</span>
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2 animate-fade-in">
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: 'var(--text-muted)' }}>Crawler type</span>
            <span className="font-mono font-medium" style={{ color: 'var(--text-secondary)' }}>{crawler.type}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: 'var(--text-muted)' }}>Reliability</span>
            <span className={`badge ${rel.badge}`}>{crawler.reliability}</span>
          </div>
          {last_seen && (
            <div className="flex items-center justify-between text-xs">
              <span style={{ color: 'var(--text-muted)' }}>Last seen</span>
              <span style={{ color: 'var(--text-secondary)' }}>{new Date(last_seen).toLocaleString()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ScrapersMonitor() {
  const qc = useQueryClient()

  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    refetchInterval: 30_000,
  })

  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: api.pipelineStatus,
    refetchInterval: 10_000,
  })

  // Build source counts from stats
  const sourceBreakdown = stats?.source_breakdown || {}
  const totalSources = Object.keys(SOURCE_META).length
  const activeSources = Object.keys(sourceBreakdown).filter(k => sourceBreakdown[k] > 0).length

  // Last run info
  const lastRun = pipelineStatus?.last_run
  const lastResult = pipelineStatus?.last_result

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wider mb-2 font-semibold" style={{ color: 'var(--text-muted)' }}>Total Sources</p>
          <p className="stat-num" style={{ color: '#93c5fd' }}>{totalSources}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Scrapers registered</p>
        </div>
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wider mb-2 font-semibold" style={{ color: 'var(--text-muted)' }}>Active Sources</p>
          <p className="stat-num" style={{ color: '#6ee7b7' }}>{activeSources}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>With data in DB</p>
        </div>
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wider mb-2 font-semibold" style={{ color: 'var(--text-muted)' }}>Last Run</p>
          <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
            {lastRun ? new Date(lastRun).toLocaleTimeString() : '—'}
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            {lastRun ? new Date(lastRun).toLocaleDateString() : 'Never'}
          </p>
        </div>
        <div className="card p-5">
          <p className="text-xs uppercase tracking-wider mb-2 font-semibold" style={{ color: 'var(--text-muted)' }}>Last Saved</p>
          <p className="stat-num" style={{ color: '#fcd34d' }}>{lastResult?.saved ?? '—'}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>ideas in last run</p>
        </div>
      </div>

      {/* Scraper pipeline explanation */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4" style={{ color: '#93c5fd' }} />
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Crawlee Pipeline Architecture</h2>
        </div>
        <div className="flex items-center gap-0 overflow-x-auto pb-2">
          {['Scrape', 'Deduplicate', 'Heuristic Filter', 'AI Analysis', 'Save to DB'].map((step, i, arr) => (
            <div key={step} className="flex items-center flex-shrink-0">
              <div
                className="px-3 py-1.5 rounded-lg text-xs font-medium"
                style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#93c5fd' }}
              >
                {step}
              </div>
              {i < arr.length - 1 && (
                <div className="mx-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>→</div>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
          Each run triggers all scrapers in parallel. Results are deduplicated against existing DB entries, scored by heuristics, and top candidates sent to the AI analysis crew (CrewAI + Groq).
        </p>
      </div>

      {/* Crawler type legend */}
      <div className="flex flex-wrap gap-2">
        {[
          { label: 'BeautifulSoupCrawler', color: 'badge-sky' },
          { label: 'PlaywrightCrawler', color: 'badge-violet' },
          { label: 'REST API', color: 'badge-green' },
          { label: 'RSS/Atom Feed', color: 'badge-amber' },
          { label: 'External API', color: 'badge-blue' },
        ].map(({ label, color }) => (
          <span key={label} className={`badge ${color}`}>{label}</span>
        ))}
        <span className="text-xs self-center ml-1" style={{ color: 'var(--text-muted)' }}>= Crawlee engine types used</span>
      </div>

      {/* Source grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array(9).fill(0).map((_, i) => (
            <div key={i} className="card p-5 h-32 skeleton" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Object.keys(SOURCE_META).map((source) => (
            <SourceCard
              key={source}
              source={source}
              count={sourceBreakdown[source] ?? 0}
            />
          ))}
        </div>
      )}

      {/* Playwright warning */}
      <div className="card p-4 flex items-start gap-3" style={{ borderColor: 'rgba(245,158,11,0.2)', background: 'rgba(245,158,11,0.05)' }}>
        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#fcd34d' }} />
        <div>
          <p className="text-xs font-semibold mb-0.5" style={{ color: '#fcd34d' }}>Anti-Bot Notice</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Upwork, Fiverr, G2, and Capterra use aggressive Cloudflare/DataDome bot protection.
            Playwright crawlers may return 0 results without high-quality rotating proxies. GitHub uses
            the Search API (no auth required, rate limited to 10 req/min). Product Hunt automatically
            falls back to its Atom RSS feed when the Playwright crawler is blocked.
          </p>
        </div>
      </div>
    </div>
  )
}
