-- V5.8 Phase D — Automation Controller / Pipeline Jobs

-- Pipeline jobs — one per content piece, tracks stage progression
CREATE TABLE IF NOT EXISTS pipeline_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL DEFAULT 0,
  channel_name TEXT DEFAULT '',
  idea_id INTEGER DEFAULT 0,
  brief_id INTEGER DEFAULT 0,
  project_id INTEGER DEFAULT 0,

  -- Current stage
  stage TEXT NOT NULL DEFAULT 'idea_pending',
  status TEXT NOT NULL DEFAULT 'queued',   -- queued | running | paused | review | completed | failed

  -- Stage timestamps (JSON for flexibility)
  stage_history_json TEXT DEFAULT '[]',
  current_stage_started_at TEXT DEFAULT '',

  -- Retry/error
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  last_error TEXT DEFAULT '',
  last_error_stage TEXT DEFAULT '',

  -- Output references
  script_text TEXT DEFAULT '',
  match_run_id INTEGER DEFAULT 0,
  render_path TEXT DEFAULT '',
  publish_data_json TEXT DEFAULT '{}',

  -- Cost tracking
  estimated_cost_usd REAL DEFAULT 0,
  provider_usage_json TEXT DEFAULT '{}',

  -- Priority
  priority INTEGER DEFAULT 50,   -- 0=highest, 100=lowest

  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_stage ON pipeline_jobs(stage, status);
CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_ws ON pipeline_jobs(workspace_id, status);

-- Channel automation policy
CREATE TABLE IF NOT EXISTS channel_automation_policy (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL UNIQUE,
  channel_name TEXT DEFAULT '',
  content_niche TEXT DEFAULT '',
  preferred_language TEXT DEFAULT 'en',
  review_strictness TEXT DEFAULT 'medium',       -- low | medium | high
  max_daily_videos INTEGER DEFAULT 3,
  quality_threshold REAL DEFAULT 0.65,
  auto_publish INTEGER DEFAULT 0,                -- 0=require approval, 1=auto
  thumbnail_enabled INTEGER DEFAULT 1,
  preferred_providers TEXT DEFAULT 'local,pexels,pixabay',
  cost_limit_daily_usd REAL DEFAULT 5.0,
  notes TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
