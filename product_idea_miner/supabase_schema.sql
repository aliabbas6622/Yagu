CREATE TABLE ideas (
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

-- Index for fast digest queries
CREATE INDEX idx_total_score ON ideas (total_score DESC);
CREATE INDEX idx_digest ON ideas (sent_in_digest, total_score DESC);
