-- V5.7 Media Intelligence Layer
-- 4 bảng cho asset management, embeddings, match runs, match items

-- Asset library (upgrade existing media_assets)
CREATE TABLE IF NOT EXISTS media_assets_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_key TEXT UNIQUE NOT NULL,
  provider TEXT NOT NULL,
  source_id TEXT DEFAULT '',
  source_url TEXT DEFAULT '',
  local_path TEXT DEFAULT '',
  asset_type TEXT NOT NULL,
  width INTEGER DEFAULT 0,
  height INTEGER DEFAULT 0,
  duration_sec REAL DEFAULT 0,
  fps REAL DEFAULT 0,
  tags_json TEXT DEFAULT '[]',
  license_notes TEXT DEFAULT '',
  preview_frames_json TEXT DEFAULT '[]',
  embedding_status TEXT DEFAULT 'pending',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Asset embeddings (vector references)
CREATE TABLE IF NOT EXISTS asset_embeddings_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL,
  frame_path TEXT DEFAULT '',
  model_name TEXT NOT NULL,
  vector_dim INTEGER NOT NULL,
  vector_store_key TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- Match runs (one per project/script)
CREATE TABLE IF NOT EXISTS scene_match_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER DEFAULT 0,
  channel_name TEXT DEFAULT '',
  model_name TEXT NOT NULL DEFAULT 'heuristic',
  total_scenes INTEGER DEFAULT 0,
  matched_scenes INTEGER DEFAULT 0,
  review_scenes INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  summary_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);

-- Match items (one per scene per run)
CREATE TABLE IF NOT EXISTS scene_match_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  scene_index INTEGER NOT NULL,
  spoken_text TEXT DEFAULT '',
  visual_goal TEXT DEFAULT '',
  selected_asset_id INTEGER DEFAULT 0,
  selected_segment_start REAL DEFAULT 0,
  selected_segment_end REAL DEFAULT 0,
  confidence_score REAL DEFAULT 0,
  confidence_label TEXT DEFAULT 'low',
  fallback_used TEXT DEFAULT '',
  requires_review INTEGER DEFAULT 0,
  candidates_json TEXT DEFAULT '[]',
  explain_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);
