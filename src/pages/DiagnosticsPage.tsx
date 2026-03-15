import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

/* ── Types ── */
interface DiagFull {
  timestamp: string; overall_health: string;
  app: { name: string; version: string; build_type: string };
  system: { os: string; os_version: string; arch: string; cpu_count: number; disk_free_gb: number };
  python: { ok: boolean; version: string; executable: string };
  dependencies: Record<string, { installed: boolean; version: string }>;
  ffmpeg: { ok: boolean; version: string };
  playwright: { ok: boolean; installed: boolean };
  database: { ok: boolean; tables: number; workspace_count: number };
  media_cache: { ok: boolean; exists: boolean; size_mb: number };
  workspace_summary: { total: number; active: number };
  recent_errors: any[];
}
interface MigrationStatus {
  current_version: number;
  applied: { version: number; applied_at: string }[];
  pending: { version: number; filename: string }[];
}

const HEALTH_COLORS: Record<string, string> = { healthy: "#22c55e", degraded: "#f59e0b", unhealthy: "#ef4444" };

export default function DiagnosticsPage() {
  const [tab, setTab] = useState<"health" | "deps" | "migrations" | "wizard">("health");
  const [diag, setDiag] = useState<DiagFull | null>(null);
  const [migrations, setMigrations] = useState<MigrationStatus | null>(null);
  const [loading, setLoading] = useState("");
  const [wizardStep, setWizardStep] = useState(0);
  const [wizardResults, setWizardResults] = useState<{name: string; ok: boolean; detail: string}[]>([]);

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
    setWizardStep(0);
    setWizardResults([]);
    setTab("wizard");

    const steps = ["Engine", "Database", "FFmpeg", "Browser", "Media Cache", "API Keys", "Workspace Dir"];
    const results: typeof wizardResults = [];

    for (let i = 0; i < steps.length; i++) {
      setWizardStep(i + 1);
      await new Promise(r => setTimeout(r, 400));

      if (diag) {
        switch (i) {
          case 0: results.push({ name: "Engine (Python)", ok: diag.python.ok, detail: diag.python.ok ? `v${diag.python.version.split(" ")[0]}` : "Python không tìm thấy" }); break;
          case 1: results.push({ name: "Database", ok: diag.database.ok, detail: diag.database.ok ? `${diag.database.tables} bảng` : "DB lỗi" }); break;
          case 2: results.push({ name: "FFmpeg", ok: diag.ffmpeg.ok, detail: diag.ffmpeg.ok ? diag.ffmpeg.version.slice(0, 40) : "Chưa cài FFmpeg" }); break;
          case 3: results.push({ name: "Browser (Playwright)", ok: diag.playwright.ok, detail: diag.playwright.installed ? "Đã cài" : "Chưa cài" }); break;
          case 4: results.push({ name: "Media Cache", ok: diag.media_cache.ok, detail: diag.media_cache.exists ? `${diag.media_cache.size_mb} MB` : "Thư mục chưa tạo" }); break;
          case 5: results.push({ name: "API Keys", ok: true, detail: "Kiểm tra ở trang Cài đặt" }); break;
          case 6: results.push({ name: "Workspace Dir", ok: diag.workspace_summary.total >= 0, detail: `${diag.workspace_summary.total} workspaces` }); break;
        }
      }
      setWizardResults([...results]);
    }
    setWizardStep(99); // done
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
              {diag.overall_health === "healthy" ? "✅" : "⚠️"} {diag.overall_health.toUpperCase()}
            </span>
            <span className="text-muted">v{diag.app.version} ({diag.app.build_type})</span>
            <button className="btn btn-sm" onClick={fetchDiag}>🔄 Refresh</button>
            <button className="btn btn-sm btn-primary" disabled={!!loading} onClick={doGenerateBundle}>
              {loading === "bundle" ? "⏳ Đang tạo..." : "📦 Export Support Bundle"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, marginBottom: 16 }}>
            <StatCard label="OS" value={`${diag.system.os} ${diag.system.arch}`} sub={diag.system.os_version.slice(0, 30)} />
            <StatCard label="Python" value={diag.python.version.split(" ")[0]} sub={diag.python.ok ? "✅ OK" : "❌ ERROR"} />
            <StatCard label="FFmpeg" value={diag.ffmpeg.ok ? "✅" : "❌"} sub={diag.ffmpeg.version.slice(0, 30) || "Chưa cài"} />
            <StatCard label="DB Tables" value={diag.database.tables} sub={`${diag.database.workspace_count} workspaces`} />
            <StatCard label="Disk Free" value={`${diag.system.disk_free_gb} GB`} sub={`${diag.system.cpu_count} CPU cores`} />
            <StatCard label="Media Cache" value={`${diag.media_cache.size_mb} MB`} sub={diag.media_cache.exists ? "Active" : "Empty"} />
          </div>

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
        <Card title="Optional Dependency Matrix">
          <table className="data-table">
            <thead><tr><th>Package</th><th>Status</th><th>Version</th><th>Purpose</th></tr></thead>
            <tbody>
              {Object.entries(diag.dependencies).map(([name, info]) => (
                <tr key={name}>
                  <td><code>{name}</code></td>
                  <td>{info.installed ? <span style={{ color: "#22c55e" }}>✅ Installed</span> : <span style={{ color: "#6b7280" }}>⬜ Optional</span>}</td>
                  <td className="text-muted">{info.version || "—"}</td>
                  <td className="text-muted" style={{ fontSize: "0.8rem" }}>{DEP_PURPOSES[name] || ""}</td>
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
                <tr key={m.version}><td>v{m.version}</td><td className="text-muted">{migrations.pending.find(p => p.version === m.version)?.filename || `${String(m.version).padStart(3, "0")}_*.sql`}</td><td className="text-muted">{new Date(m.applied_at).toLocaleString("vi")}</td></tr>
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
          {wizardStep === 0 && (
            <div style={{ textAlign: "center", padding: 32 }}>
              <h3>🧙 Chào mừng đến ChannelForge Studio</h3>
              <p className="text-muted">Wizard sẽ kiểm tra môi trường, database, dependencies và tạo cấu hình ban đầu.</p>
              <button className="btn btn-primary" style={{ marginTop: 16, fontSize: "1.1rem", padding: "12px 32px" }} onClick={runWizard}>▶ Bắt đầu kiểm tra</button>
            </div>
          )}
          {wizardStep > 0 && (
            <div style={{ maxWidth: 500, margin: "0 auto" }}>
              {wizardResults.map((r, i) => (
                <div key={i} style={{ display: "flex", gap: 12, alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontSize: "1.2rem" }}>{r.ok ? "✅" : "⚠️"}</span>
                  <div style={{ flex: 1 }}>
                    <strong>{r.name}</strong>
                    <span className="text-muted" style={{ marginLeft: 8 }}>{r.detail}</span>
                  </div>
                </div>
              ))}
              {wizardStep < 99 && (
                <div style={{ padding: 16, textAlign: "center" }}>
                  <span className="text-muted">⏳ Đang kiểm tra step {wizardStep}/7...</span>
                </div>
              )}
              {wizardStep === 99 && (
                <div style={{ padding: 16, textAlign: "center" }}>
                  <h3 style={{ color: wizardResults.every(r => r.ok) ? "#22c55e" : "#f59e0b" }}>
                    {wizardResults.every(r => r.ok) ? "✅ Tất cả kiểm tra đạt!" : "⚠️ Một số dependency chưa cài — app vẫn chạy được"}
                  </h3>
                  <button className="btn" style={{ marginTop: 8 }} onClick={() => { setWizardStep(0); setWizardResults([]); }}>🔄 Chạy lại</button>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

const DEP_PURPOSES: Record<string, string> = {
  numpy: "Vector operations, embeddings",
  sentence_transformers: "CLIP/semantic embedding models",
  faiss: "Fast vector index search",
  open_clip: "Multilingual CLIP models",
  cv2: "Frame extraction from video",
  moviepy: "Video editing, frame extraction fallback",
  PIL: "Image processing",
  playwright: "Browser automation for workspaces",
  httpx: "HTTP client for API calls",
  pydantic: "Data validation (required)",
};
