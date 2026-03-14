-- Migration 003: Audit Log system
-- Track all system operations for transparency

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT DEFAULT '',
    entity_id INTEGER DEFAULT 0,
    channel_name TEXT DEFAULT '',
    details TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    model TEXT DEFAULT '',
    tokens_used INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_channel ON audit_logs(channel_name, created_at DESC);

INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (3, datetime('now'));
