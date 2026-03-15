-- V5.6 Workspace Supervisor + Network Policy Manager
-- 4 bảng mới cho workspace lifecycle, route bindings, network policies, session checks

-- Snapshot runtime state cho mỗi workspace
CREATE TABLE IF NOT EXISTS workspace_runtime_state (
  workspace_id INTEGER PRIMARY KEY,
  runtime_status TEXT NOT NULL DEFAULT 'stopped',
  browser_pid INTEGER DEFAULT 0,
  browser_type TEXT DEFAULT 'chromium',
  context_attached INTEGER DEFAULT 0,
  last_launch_at TEXT DEFAULT '',
  last_seen_alive_at TEXT DEFAULT '',
  last_close_at TEXT DEFAULT '',
  last_error_code TEXT DEFAULT '',
  last_error_message TEXT DEFAULT '',
  current_route_mode TEXT DEFAULT 'DIRECT',
  current_outbound_ip TEXT DEFAULT '',
  updated_at TEXT NOT NULL
);

-- Route profile binding cho workspace
CREATE TABLE IF NOT EXISTS workspace_route_bindings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL,
  route_profile_id INTEGER NOT NULL,
  bind_mode TEXT NOT NULL DEFAULT 'studio_only',
  active INTEGER NOT NULL DEFAULT 1,
  notes TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Log network policy decisions
CREATE TABLE IF NOT EXISTS network_policy_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER DEFAULT 0,
  job_id INTEGER DEFAULT 0,
  job_type TEXT NOT NULL,
  policy_mode TEXT NOT NULL,
  route_profile_id INTEGER DEFAULT 0,
  decision TEXT NOT NULL,
  outbound_ip TEXT DEFAULT '',
  evidence_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);

-- Session verification checks
CREATE TABLE IF NOT EXISTS workspace_session_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL,
  check_type TEXT NOT NULL,
  status TEXT NOT NULL,
  details_json TEXT DEFAULT '{}',
  screenshot_path TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
