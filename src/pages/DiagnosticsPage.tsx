import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

/* ── Types ── */
interface CheckResult {
  ok: boolean; severity: string; message: string; fix: string; blocks: string;
  [key: string]: any;
}
interface DiagFull {
  timestamp: string; overall_health: string;
  app: { name: string; version: string; build_type: string };
  system: { os: string; os_version: string; arch: string; cpu_count: number; disk_free_gb: number };
  checks: Record<string, CheckResult>;
  dependencies: Record<string, { installed: boolean; version: string; purpose: string; install?: string }>;
  workspace_summary: { total: number; active: number };
  recent_errors: any[];
}
interface MigrationStatus {
  current_version: number;
  applied: { version: number; applied_at: string }[];
  available: { version: number; filename: string }[];
  pending: { version: number; filename: string }[];
}
interface ReadinessReport {
  ok: boolean; status: string; version: string;
  checks: Record<string, CheckResult>;
  summary: { passed: number; warnings: number; blockers: number; total: number };
  blocker_names: string[];
  warning_names: string[];
}

const HEALTH_COLORS: Record<string, string> = { healthy: "#22c55e", degraded: "#f59e0b", blocked: "#ef4444" };
const SEV_COLORS: Record<string, string> = { critical: "#ef4444", warning: "#f59e0b", info: "#6b7280" };
const CHECK_LABELS: Record<string, string> = {
  python: "🐍 Python Runtime", database: "🗄️ Database",
  ffmpeg: "🎬 FFmpeg", playwright: "🌐 Browser (Playwright)",
  writable_dirs: "📁 Writable Dirs", api_keys: "🔑 API Keys",
  media_cache: "💾 Media Cache", migrations: "🔄 Migrations",
};

export default function DiagnosticsPage() {
  const [tab, setTab] = useState<"health" | "deps" | "migrations" | "wizard">("health");
  const [diag, setDiag] = useState<DiagFull | null>(null);
  const [migrations, setMigrations] = useState<MigrationStatus | null>(null);
  const [loading, setLoading] = useState("");
  const [readiness, setReadiness] = useState<ReadinessReport | null>(null);
  const [wizardRunning, setWizardRunning] = useState(false);

  const fetchDiag = () => { api.get<DiagFull>("/api/v5/system/diagnostics/full").then(setDiag).catch(() => {}); };
  const fetchMigrations = () => { api.get<MigrationStatus>("/api/v5/system/migrations/status").then(setMigrations).catch(() => {}); };
  useEffect(() => { fetchDiag(); fetchMigrations(); }, []);

  const doGenerateBundle = async () => {
    setLoading("bundle");
    await api.post("/api/v5/system/diagnostics/support-bundle").catch(() => {});
    setLoading("");
    alert("Support bundle đã tạo trong thư mục engine/data/");
  };

  const doRunMigrations = async () => {
    setLoading("migrate");
    await api.post("/api/v5/system/migrations/run").catch(() => {});
    fetchMigrations();
    setLoading("");
  };

  const runWizard = async () => {
    setWizardRunning(true);
    setReadiness(null);
    setTab("wizard");
    try {
      const result = await api.get<ReadinessReport>("/api/v5/system/readiness");
      setReadiness(result);
    } catch {
      setReadiness(null);
    }
    setWizardRunning(false);
  };

  const TABS = [
    { key: "health", label: "🏥 Health" },
    { key: "deps", label: "📦 Dependencies" },
    { key: "migrations", label: "🔄 Migrations" },
    { key: "wizard", label: "🧙 First-Run Wizard" },
  ] as const;

  return (
    <div>
      <h2>Chẩn đoán & Đóng gói</h2>
      <p className="text-muted">Kiểm tra sức khỏe hệ thống, dependency matrix, migrations, first-run wizard.</p>

      <div className="tab-bar" style={{ marginBottom: 16 }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn${tab === t.key ? " active" : ""}`} onClick={() => setTab(t.key as typeof tab)}>{t.label}</button>
        ))}
      </div>

      {/* ── HEALTH TAB ── */}
      {tab === "health" && diag && (
        <div>
          <div style={{ display: "flex", gap: 16, marginBottom: 16, alignItems: "center" }}>
            <span style={{ fontSize: "1.5rem", fontWeight: 700, color: HEALTH_COLORS[diag.overall_health] || "#6b7280" }}>
              {diag.overall_health === "healthy" ? "✅" : diag.overall_health === "blocked" ? "❌" : "⚠️"} {diag.overall_health.toUpperCase()}
            </span>
            <span className="text-muted">v{diag.app.version} ({diag.app.build_type})</span>
            <button className="btn btn-sm" onClick={fetchDiag}>🔄 Refresh</button>
            <button className="btn btn-sm btn-primary" disabled={!!loading} onClick={doGenerateBundle}>
              {loading === "bundle" ? "⏳ Đang tạo..." : "📦 Export Support Bundle"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, marginBottom: 16 }}>
            <StatCard label="OS" value={`${diag.system.os} ${diag.system.arch}`} sub={diag.system.os_version.slice(0, 30)} />
            <StatCard label="Disk Free" value={`${diag.system.disk_free_gb} GB`} sub={`${diag.system.cpu_count} CPU cores`} />
          </div>

          {/* Structured checks */}
          <Card title="System Checks">
            {Object.entries(diag.checks).map(([key, check]) => (
              <div key={key} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                <span style={{ fontSize: "1.2rem", minWidth: 28 }}>{check.ok ? "✅" : check.severity === "critical" ? "❌" : "⚠️"}</span>
                <div style={{ flex: 1 }}>
                  <strong>{CHECK_LABELS[key] || key}</strong>
                  <span className="text-muted" style={{ marginLeft: 8 }}>{check.message}</span>
                  {!check.ok && check.fix && (
                    <div style={{ marginTop: 4, fontSize: "0.82rem", color: SEV_COLORS[check.severity] || "#6b7280" }}>
                      💡 Fix: {check.fix}
                      {check.blocks !== "none" && <span style={{ marginLeft: 8, fontWeight: 600 }}>({check.blocks === "boot" ? "Blocks app boot" : "Blocks some features"})</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </Card>

          {diag.recent_errors.length > 0 && (
            <Card title="Lỗi gần đây">
              {diag.recent_errors.map((err: any, i: number) => (
                <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)", fontSize: "0.85rem" }}>
                  <strong style={{ color: "#ef4444" }}>{err.error_type}</strong>: {err.error_message?.slice(0, 200)}
                  <span className="text-muted" style={{ marginLeft: 8 }}>{err.created_at}</span>
                </div>
              ))}
            </Card>
          )}
        </div>
      )}

      {/* ── DEPS TAB ── */}
      {tab === "deps" && diag && (
        <Card title="Dependency Matrix">
          <table className="data-table">
            <thead><tr><th>Package</th><th>Status</th><th>Version</th><th>Purpose</th><th>Install</th></tr></thead>
            <tbody>
              {Object.entries(diag.dependencies).map(([name, info]) => (
                <tr key={name}>
                  <td><code>{name}</code></td>
                  <td>{info.installed ? <span style={{ color: "#22c55e" }}>✅ Installed</span> : <span style={{ color: "#6b7280" }}>⬜ Optional</span>}</td>
                  <td className="text-muted">{info.version || "—"}</td>
                  <td className="text-muted" style={{ fontSize: "0.8rem" }}>{info.purpose || ""}</td>
                  <td className="text-muted" style={{ fontSize: "0.75rem" }}>{!info.installed && info.install ? <code>{info.install}</code> : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── MIGRATIONS TAB ── */}
      {tab === "migrations" && migrations && (
        <Card title={`Database Migrations (v${migrations.current_version})`}>
          {migrations.pending.length > 0 && (
            <div style={{ marginBottom: 12, padding: 12, background: "rgba(245,158,11,0.15)", borderRadius: 8 }}>
              <strong style={{ color: "#f59e0b" }}>⚠️ {migrations.pending.length} migration(s) pending</strong>
              <button className="btn btn-sm btn-primary" style={{ marginLeft: 12 }} disabled={!!loading} onClick={doRunMigrations}>
                {loading === "migrate" ? "⏳ Running..." : "▶ Run Migrations"}
              </button>
            </div>
          )}
          <table className="data-table">
            <thead><tr><th>Version</th><th>Filename</th><th>Applied At</th></tr></thead>
            <tbody>
              {migrations.applied.map(m => (
                <tr key={m.version}><td>v{m.version}</td><td className="text-muted">{migrations.available?.find((p: any) => p.version === m.version)?.filename || `${String(m.version).padStart(3, "0")}_*.sql`}</td><td className="text-muted">{new Date(m.applied_at).toLocaleString("vi")}</td></tr>
              ))}
              {migrations.pending.map(m => (
                <tr key={m.version} style={{ opacity: 0.6 }}><td>v{m.version} <span style={{ color: "#f59e0b" }}>⏳</span></td><td>{m.filename}</td><td className="text-muted">Pending</td></tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── WIZARD TAB ── */}
      {tab === "wizard" && (
        <Card title="First-Run Setup Wizard">
          {!readiness && !wizardRunning && (
            <div style={{ textAlign: "center", padding: 32 }}>
              <h3>🧙 Chào mừng đến ChannelForge Studio</h3>
              <p className="text-muted">Wizard sẽ kiểm tra toàn bộ môi trường thông qua backend readiness API.</p>
              <button className="btn btn-primary" style={{ marginTop: 16, fontSize: "1.1rem", padding: "12px 32px" }} onClick={runWizard}>▶ Bắt đầu kiểm tra</button>
            </div>
          )}
          {wizardRunning && (
            <div style={{ textAlign: "center", padding: 32 }}>
              <span className="text-muted">⏳ Đang kiểm tra hệ thống...</span>
            </div>
          )}
          {readiness && (
            <div style={{ maxWidth: 600, margin: "0 auto" }}>
              {/* Summary bar */}
              <div style={{ display: "flex", gap: 16, marginBottom: 16, justifyContent: "center" }}>
                <span style={{ color: "#22c55e", fontWeight: 600 }}>✅ {readiness.summary.passed} passed</span>
                {readiness.summary.warnings > 0 && <span style={{ color: "#f59e0b", fontWeight: 600 }}>⚠️ {readiness.summary.warnings} warnings</span>}
                {readiness.summary.blockers > 0 && <span style={{ color: "#ef4444", fontWeight: 600 }}>❌ {readiness.summary.blockers} blockers</span>}
              </div>

              {/* Check list */}
              {Object.entries(readiness.checks).map(([key, check]) => (
                <div key={key} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "12px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontSize: "1.3rem", minWidth: 32 }}>{check.ok ? "✅" : check.severity === "critical" ? "❌" : "⚠️"}</span>
                  <div style={{ flex: 1 }}>
                    <strong>{CHECK_LABELS[key] || key}</strong>
                    <div className="text-muted" style={{ marginTop: 2 }}>{check.message}</div>
                    {!check.ok && check.fix && (
                      <div style={{ marginTop: 4, fontSize: "0.82rem", padding: "6px 10px", background: "rgba(245,158,11,0.1)", borderRadius: 6, color: SEV_COLORS[check.severity] }}>
                        💡 {check.fix}
                        {check.blocks === "boot" && <strong style={{ marginLeft: 6 }}> — ⛔ Blocks app boot</strong>}
                        {check.blocks === "feature_subset" && <span style={{ marginLeft: 6 }}> — chỉ ảnh hưởng một số tính năng</span>}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Final status */}
              <div style={{ padding: 20, textAlign: "center", marginTop: 16 }}>
                <h3 style={{ color: readiness.status === "ready" ? "#22c55e" : readiness.status === "degraded" ? "#f59e0b" : "#ef4444" }}>
                  {readiness.status === "ready" ? "✅ Hệ thống sẵn sàng!" :
                   readiness.status === "degraded" ? "⚠️ Hoạt động được — một số tính năng bị hạn chế" :
                   "❌ Blocked — cần sửa lỗi critical trước"}
                </h3>
                <p className="text-muted">v{readiness.version}</p>
                <button className="btn" style={{ marginTop: 8 }} onClick={runWizard}>🔄 Chạy lại</button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
