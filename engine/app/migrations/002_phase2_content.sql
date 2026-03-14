-- Migration 002: Phase 2 — Research Library, Content Studio, Templates
-- Adds: research_snapshots, content_ideas, content_briefs,
--        script_drafts, template_packs, cost_ledger

CREATE TABLE IF NOT EXISTS research_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT,
    title TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    source_title TEXT DEFAULT '',
    extractor TEXT DEFAULT '',
    cleaned_text TEXT DEFAULT '',
    metadata_json TEXT DEFAULT '{}',
    relevance_score REAL DEFAULT 0.0,
    tags TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_channel ON research_snapshots(channel_name, created_at DESC);

CREATE TABLE IF NOT EXISTS content_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    title TEXT NOT NULL,
    angle TEXT DEFAULT '',
    source TEXT DEFAULT '',
    status TEXT DEFAULT 'inbox',
    priority INTEGER DEFAULT 100,
    research_ids TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON content_ideas(channel_name, status, priority);

CREATE TABLE IF NOT EXISTS content_briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER REFERENCES content_ideas(id),
    channel_name TEXT NOT NULL,
    title TEXT NOT NULL,
    target_format TEXT DEFAULT 'shorts',
    outline_json TEXT DEFAULT '{}',
    target_duration_sec INTEGER DEFAULT 60,
    voice_style TEXT DEFAULT '',
    footage_style TEXT DEFAULT '',
    thumbnail_notes TEXT DEFAULT '',
    cta_text TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS script_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER REFERENCES content_briefs(id),
    channel_name TEXT NOT NULL,
    title TEXT NOT NULL,
    script_text TEXT DEFAULT '',
    script_json TEXT DEFAULT '{}',
    word_count INTEGER DEFAULT 0,
    estimated_duration_sec INTEGER DEFAULT 0,
    fact_check_status TEXT DEFAULT 'pending',
    fact_check_notes TEXT DEFAULT '',
    source_refs TEXT DEFAULT '[]',
    provider_used TEXT DEFAULT '',
    model_used TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS template_packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'shorts',
    description TEXT DEFAULT '',
    config_json TEXT DEFAULT '{}',
    is_builtin INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT,
    provider TEXT NOT NULL,
    model TEXT DEFAULT '',
    operation TEXT NOT NULL,
    input_units INTEGER DEFAULT 0,
    output_units INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0.0,
    job_id INTEGER,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cost_channel ON cost_ledger(channel_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_provider ON cost_ledger(provider, created_at DESC);

INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (2, datetime('now'));
