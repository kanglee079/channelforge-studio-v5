-- V5.8 Packaging & Installer Hardening
-- Tables for app configuration, first-run wizard state, crash logs

-- App-level configuration (key-value store)
CREATE TABLE IF NOT EXISTS app_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- First-run wizard completion tracking
CREATE TABLE IF NOT EXISTS first_run_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  step_name TEXT NOT NULL,
  status TEXT NOT NULL,
  details_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);

-- Crash/Error logs for support bundle
CREATE TABLE IF NOT EXISTS crash_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  error_type TEXT NOT NULL,
  error_message TEXT NOT NULL,
  traceback TEXT DEFAULT '',
  context_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);
