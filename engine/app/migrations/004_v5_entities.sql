-- Migration 004: V5 Entities
-- Adds: media_assets, scene_match_results, scene_match_candidates, asset_embeddings,
--        trend_items, topic_clusters, channel_trend_scores, research_packs,
--        review_items, analytics_daily, provider_usage_events, budget_profiles,
--        proxy_profiles, workspace_health_events
-- Extends: workspaces table

-- ═══════════════════════════════════════════════════════════
-- V5.1 — Visual Match Engine
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS media_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL DEFAULT 'video',       -- video, image, audio
    source_provider TEXT DEFAULT '',                  -- pexels, pixabay, local, manual
    source_url TEXT DEFAULT '',
    source_id TEXT DEFAULT '',                        -- provider-specific ID
    local_path TEXT DEFAULT '',
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    duration_sec REAL DEFAULT 0.0,
    aspect_ratio TEXT DEFAULT '',
    language_hint TEXT DEFAULT '',
    tags_json TEXT DEFAULT '[]',
    embedding_status TEXT DEFAULT 'pending',          -- pending, done, failed
    license_notes TEXT DEFAULT '',
    quality_score REAL DEFAULT 0.0,
    phash TEXT DEFAULT '',                            -- perceptual hash
    sha256 TEXT DEFAULT '',
    usage_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_provider ON media_assets(source_provider, asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_phash ON media_assets(phash);

CREATE TABLE IF NOT EXISTS scene_match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_project_id INTEGER,                       -- references script_drafts.id
    channel_name TEXT DEFAULT '',
    scene_index INTEGER NOT NULL,
    scene_json TEXT DEFAULT '{}',                     -- visual_intent, must_have_objects, mood, etc.
    selected_asset_id INTEGER,
    selected_clip_start_sec REAL DEFAULT 0.0,
    selected_clip_end_sec REAL DEFAULT 0.0,
    final_score REAL DEFAULT 0.0,
    confidence_label TEXT DEFAULT 'low',              -- low, medium, high
    status TEXT DEFAULT 'pending',                    -- pending, matched, pinned, review, failed
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scene_match_project ON scene_match_results(script_project_id, scene_index);

CREATE TABLE IF NOT EXISTS scene_match_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_match_result_id INTEGER REFERENCES scene_match_results(id),
    asset_id INTEGER REFERENCES media_assets(id),
    semantic_score REAL DEFAULT 0.0,
    object_match_score REAL DEFAULT 0.0,
    style_match_score REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    negative_penalty REAL DEFAULT 0.0,
    duplicate_penalty REAL DEFAULT 0.0,
    final_score REAL DEFAULT 0.0,
    explain_json TEXT DEFAULT '{}',
    rank INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_candidates_scene ON scene_match_candidates(scene_match_result_id, final_score DESC);

CREATE TABLE IF NOT EXISTS asset_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER REFERENCES media_assets(id),
    embedding_model TEXT DEFAULT 'clip-vit-b-32',
    vector_dim INTEGER DEFAULT 512,
    vector_blob_path TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embeddings_asset ON asset_embeddings(asset_id);

-- ═══════════════════════════════════════════════════════════
-- V5.4 — Research / Trend Assistant 2.0
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS trend_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,                        -- google_trends, newsapi, gdelt, rss, manual
    source_ref TEXT DEFAULT '',
    title TEXT NOT NULL,
    snippet TEXT DEFAULT '',
    url TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    region TEXT DEFAULT '',
    fetched_at TEXT NOT NULL,
    freshness_score REAL DEFAULT 0.0,
    source_confidence_score REAL DEFAULT 0.5,
    raw_json TEXT DEFAULT '{}',
    normalized_hash TEXT DEFAULT '',
    status TEXT DEFAULT 'new'                         -- new, scored, used, dismissed
);
CREATE INDEX IF NOT EXISTS idx_trends_source ON trend_items(source_type, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_trends_hash ON trend_items(normalized_hash);

CREATE TABLE IF NOT EXISTS topic_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_topic TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]',
    cluster_score REAL DEFAULT 0.0,
    trend_item_ids TEXT DEFAULT '[]',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clusters_topic ON topic_clusters(canonical_topic);

CREATE TABLE IF NOT EXISTS channel_trend_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    trend_item_id INTEGER REFERENCES trend_items(id),
    relevance_score REAL DEFAULT 0.0,
    monetization_score REAL DEFAULT 0.0,
    contentability_score REAL DEFAULT 0.0,
    risk_score REAL DEFAULT 0.0,
    final_score REAL DEFAULT 0.0,
    recommended_action TEXT DEFAULT '',               -- produce, research, skip, watch
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cts_channel ON channel_trend_scores(channel_name, final_score DESC);

CREATE TABLE IF NOT EXISTS research_packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT DEFAULT '',
    idea_id INTEGER,
    summary_json TEXT DEFAULT '{}',
    source_refs_json TEXT DEFAULT '[]',
    fact_blocks_json TEXT DEFAULT '[]',
    visual_opportunities_json TEXT DEFAULT '[]',
    risk_notes_json TEXT DEFAULT '[]',
    hook_suggestion TEXT DEFAULT '',
    cta_suggestion TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    name TEXT NOT NULL,
    watch_type TEXT DEFAULT 'keyword',                -- keyword, entity, competitor, domain
    query TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    last_refresh_at TEXT,
    alert_on_spike INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_watchlists_channel ON watchlists(channel_name, active);

-- ═══════════════════════════════════════════════════════════
-- V5.5 — Review + Analytics + Cost Router
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_type TEXT NOT NULL,                        -- scene_low_conf, source_risk, policy_conflict, upload_approval, budget_anomaly, asset_repeat
    object_type TEXT DEFAULT '',                      -- scene, research, idea, job, upload
    object_id INTEGER DEFAULT 0,
    channel_name TEXT DEFAULT '',
    priority INTEGER DEFAULT 100,
    reason_code TEXT DEFAULT '',
    reason_text TEXT DEFAULT '',
    score REAL DEFAULT 0.0,
    payload_json TEXT DEFAULT '{}',
    status TEXT DEFAULT 'open',                       -- open, approved, rejected, escalated
    resolved_by TEXT DEFAULT '',
    resolved_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_status ON review_items(status, priority ASC);
CREATE INDEX IF NOT EXISTS idx_review_channel ON review_items(channel_name, status);

CREATE TABLE IF NOT EXISTS analytics_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    day TEXT NOT NULL,
    jobs_created INTEGER DEFAULT 0,
    jobs_completed INTEGER DEFAULT 0,
    jobs_failed INTEGER DEFAULT 0,
    videos_rendered INTEGER DEFAULT 0,
    uploads_completed INTEGER DEFAULT 0,
    avg_scene_confidence REAL DEFAULT 0.0,
    manual_replacements INTEGER DEFAULT 0,
    total_cost_estimate REAL DEFAULT 0.0,
    UNIQUE(channel_name, day)
);

CREATE TABLE IF NOT EXISTS provider_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT DEFAULT '',
    task_type TEXT NOT NULL,                          -- script, tts, stt, footage, image, research, trend
    channel_name TEXT DEFAULT '',
    job_id INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 1,
    token_count INTEGER DEFAULT 0,
    duration_sec REAL DEFAULT 0.0,
    cost_estimate REAL DEFAULT 0.0,
    cache_hit INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pue_provider ON provider_usage_events(provider, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pue_channel ON provider_usage_events(channel_name, created_at DESC);

CREATE TABLE IF NOT EXISTS budget_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    monthly_limit REAL DEFAULT 100.0,
    preferred_quality_mode TEXT DEFAULT 'budget',     -- budget, balanced, premium
    rules_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ═══════════════════════════════════════════════════════════
-- V5.2 — Workspace Engine Enhancements
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS proxy_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    protocol TEXT DEFAULT 'http',                     -- http, https, socks5
    server TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT DEFAULT '',
    password_encrypted TEXT DEFAULT '',
    bypass TEXT DEFAULT '',
    status TEXT DEFAULT 'active',                     -- active, inactive, testing, failed
    last_tested_at TEXT,
    last_test_status TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_health_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    event_type TEXT NOT NULL,                         -- check_passed, check_failed, degraded, recovered
    severity TEXT DEFAULT 'info',                     -- info, warning, error, critical
    message TEXT DEFAULT '',
    payload_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ws_health ON workspace_health_events(workspace_id, created_at DESC);

INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (4, datetime('now'));
