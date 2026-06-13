/**
 * api.js — centralized API client for the Product Idea Miner backend.
 * All functions return the parsed JSON response directly.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  // ─── Stats ──────────────────────────────────────────────────────────
  stats: () => request('/stats'),

  // ─── Ideas ──────────────────────────────────────────────────────────
  ideas: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/ideas${qs ? '?' + qs : ''}`);
  },
  idea: (id) => request(`/ideas/${id}`),
  deleteIdea: (id) => request(`/ideas/${id}`, { method: 'DELETE' }),
  markSent: (id) => request(`/ideas/${id}/mark-sent`, { method: 'PATCH' }),

  // ─── Pipeline ───────────────────────────────────────────────────────
  pipelineStatus: () => request('/scraper/status'),
  runPipeline: () => request('/trigger', { method: 'POST' }),

  // ─── Legacy trigger ─────────────────────────────────────────────────
  trigger: () => request('/trigger', { method: 'POST' }),

  // ─── Digest ─────────────────────────────────────────────────────────
  digestPreview: () => request('/digest/preview'),
  sendDigest: () => request('/digest/send', { method: 'POST' }),

  // ─── Export ─────────────────────────────────────────────────────────
  exportUrl: (format, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return `${API_BASE}/export/${format}${qs ? '?' + qs : ''}`;
  },

  // ─── Health & Settings ──────────────────────────────────────────────
  health: () => request('/health'),
  settings: () => request('/settings'),

  // ─── DB / Sync ──────────────────────────────────────────────────────
  dbStatus: () => request('/db/status'),
  syncToSupabase: () => request('/sync/to-supabase', { method: 'POST' }),

  // ─── Trends ─────────────────────────────────────────────────────────
  trends: () => request('/trends'),
};
