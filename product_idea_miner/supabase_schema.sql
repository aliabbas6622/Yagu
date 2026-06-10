CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.ideas (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source           TEXT NOT NULL,
  original_url     TEXT UNIQUE NOT NULL,
  post_title       TEXT,
  post_body        TEXT,
  problem_summary  TEXT,
  urgency_score    INT,
  frequency_score  INT,
  monetization_score INT,
  total_score      INT,
  product_ideas    JSONB,
  category         TEXT,
  target_audience  TEXT,
  date_found       TIMESTAMPTZ DEFAULT NOW(),
  sent_in_digest   BOOLEAN DEFAULT FALSE
);

ALTER TABLE public.ideas ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.ideas FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.ideas TO service_role;

-- Index for fast digest queries
CREATE INDEX IF NOT EXISTS idx_ideas_total_score ON public.ideas (total_score DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_digest ON public.ideas (sent_in_digest, total_score DESC);

-- Table for launched startups
CREATE TABLE IF NOT EXISTS public.startups (
  id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name                    TEXT NOT NULL,
  url                     TEXT UNIQUE NOT NULL,
  description             TEXT,
  country                 TEXT,
  category                TEXT,
  innovation_score        INT,
  market_potential_score  INT,
  execution_score         INT,
  total_rating           INT,
  summary                 TEXT,
  date_found              TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.startups ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.startups FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.startups TO service_role;

CREATE INDEX IF NOT EXISTS idx_startups_total_rating ON public.startups (total_rating DESC);
