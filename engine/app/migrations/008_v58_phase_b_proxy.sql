-- V5.8 Phase B — Proxy test result persistence + state machine hardening

-- Add proxy test result fields to proxy_profiles
ALTER TABLE proxy_profiles ADD COLUMN last_test_ok INTEGER DEFAULT 0;
ALTER TABLE proxy_profiles ADD COLUMN last_test_latency_ms INTEGER DEFAULT 0;
ALTER TABLE proxy_profiles ADD COLUMN last_test_ip TEXT DEFAULT '';
